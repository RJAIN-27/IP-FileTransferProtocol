from socket import *
import time 
import os
from threading import *

server= []
server_tuple = []
num_servers = 0
bytesRead = 0
DATA_INDICATOR = '0101010101010101'
DATA_INDICATOR_LAST = '1111111111111111'
ACK_INDICATOR='1010101010101010'
SEP = '&*'
ack=[]
thread_list=[]
timeout=5

def generate_checksum(data):
    s = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            w = (data[i]) + ((data[i + 1]) << 8)
            k = s + w
            s = (k & 0xffff) + (k >> 16)
    return ~s & 0xffff

def server_thread(server_tuple_single, clientSocket, packet,start_time_for_packet,i, seq_num):
    global ack
    packet_bytes = packet.encode()
    clientSocket.sendto(packet_bytes, (server_tuple_single))
    try:
        message,addr=clientSocket.recvfrom(1024)
        message = message.decode()
        time_till_now=time.time()-start_time_for_packet
        clientSocket.settimeout(timeout-time_till_now)
        msg=message.split(SEP)
        if msg[2] == ACK_INDICATOR:
            ack.append(server_tuple_single)  #add another paranthesis may be
    except:
        print("Timeout occurred for receiver ", i, ",sequence number: ", int(seq_num,2))  

def stop_and_wait(seq_no_bin,segment,LastSegmntFlg,clientSocket):
    
    global thread_list
    global ack 
    global server_tuple
    global num_servers
    

    indicator =''
    checksum = '{0:016b}'.format(generate_checksum(segment))
    if LastSegmntFlg == True:
        indicator = DATA_INDICATOR_LAST
    else :
        indicator = DATA_INDICATOR 
    header = seq_no_bin + SEP + checksum + SEP + indicator
    packet = header + SEP + (segment.decode())
    i=0

    start_time_for_packet=time.time()

    thread_list=[]
    ack=[]
    while (i<num_servers):
        thread_list.append(Thread(target=server_thread,args=(server_tuple[i], clientSocket, packet,start_time_for_packet,i, seq_no_bin)))
        thread_list[i].start()
        i+=1
    i=0
    while (i<num_servers):
        thread_list[i].join()
        i+=1
    clientSocket.settimeout(timeout)

    server_set = set(server_tuple)
    ack_set = set(ack)
    difference = server_set.union(ack_set) - server_set.intersection(ack_set)
    left_over = list(difference)

    # for tuple in server_tuple:
    #     if tuple not in ack:
    #         left_over.append(tuple)

    print ("left over : ", left_over)
    print ("Ack : ", ack)

    if (len(left_over)==0):
        print ("The packet is sent to all the receivers")
        return 
    else:    
        while(len(left_over)!=0):
            i=0
            start_time_for_packet=time.time()
            
            thread_list=[]
            ack=[]
            while(i<len(left_over)):
                thread_list.append(Thread(target=server_thread, args=(server_tuple[i], clientSocket, packet,start_time_for_packet,i,seq_no_bin)))
                thread_list[i].start()
                i+=1
            i=0
            while (i<len(left_over)):
                thread_list[i].join()
                i+=1
            clientSocket.settimeout(timeout)
            
            # left_over=[]

            # for tuple in server_tuple:
            #     if tuple not in ack:
            #         left_over.append(tuple)

            left_over_set = set(left_over)
            ack_new_set = set(ack)
            difference = left_over_set.union(ack_new_set) - left_over_set.intersection(ack_new_set)
            left_over = list(difference)

            print ("left over inside left over : ", left_over)
            print ("Ack inside left over : ", ack)

        return 

def rdt_send(filename,MSS,serverport):
    global bytesRead
    seq_no = 0
    fileSend = open(filename, 'rb+')
    FileContent = True
    LastSegmntFlg = False
    fileSend.seek(0,2)
    EOF = fileSend.tell()
    fileSend.seek(0,0)
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.settimeout(timeout)
    # TO-DO : File transfer timer for tasks ???
    while FileContent == True:
        print( "Reading next MSS")
        seq_no = seq_no + bytesRead
        print("Current seq no : ", seq_no)
        seq_no_bin = '{0:032b}'.format(seq_no)   #this is a string
        segment = fileSend.read(MSS)
        bytesRead = len(segment)
        if fileSend.tell() == EOF:
            LastSegmntFlg = True
            FileContent = False
        stop_and_wait(seq_no_bin,segment,LastSegmntFlg,clientSocket)

def main():
    global num_servers 
    global server
    global server_tuple

    command = input("Invoke sender\n")
    args = command.split(' ')
    num_args = len(args)
    num_servers = num_args- 4
    i=1
    while i <= num_servers:
        server.append(args[i])
        i = i + 1
    serverport = int(args[i])
    filename = args[i+1]
    MSS = int(args[i+2])
    file_size = os.path.getsize(filename) 
    i = 0
    while i < num_servers:
        server_tuple.append((server[i],serverport))
        i = i + 1
    # TO-DO Implement timers 
    rdt_send(filename,MSS,serverport)

if __name__ == '__main__':
    main()

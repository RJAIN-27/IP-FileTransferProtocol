import socket
import os
import random

bytesReceived=0
SEP='&*'

DATA_INDICATOR_LAST = '1111111111111111'
ACK_INDICATOR='1010101010101010'
ACK_HEADER='0000000000000000'


def carry_around_add(a, b):
    c = a + b
    d = (c & 0xffff) + (c >> 16)
    return d

def check_checksum(data,checksum):                     #To generate and sum 16-bit words from application data and compare it with the received checksum
    s = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            w = (data[i]) + ((data[i + 1]) << 8)
            k = s + w
            s = (k & 0xffff) + (k >> 16)
    cal_check_sum = s & 0xffff
    cal_check_sum1 = ~s & 0xffff
    print("calculated", cal_check_sum1)
    print("recieved", int(checksum,2))
    print("The and is", cal_check_sum & int(checksum,2))

    return cal_check_sum & int(checksum,2)
    
def main():
    command = input("Invoke receiver\n")
    args = command.split(' ')
    num_args = len(args)
    serverport=int(args[1])
    filename=args[2]
    probablity=float(args[3])

    ServerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ServerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    ServerSock.settimeout(60)
    server_address = ('',serverport)
    print ("\nStarting up SERVER on %s port %s" %(server_address))
    ServerSock.bind(server_address)

    seq_num = 0

    file_received = open(filename,"wb")

    while True:
        data_bytes, client_address = ServerSock.recvfrom(2048)
        data=data_bytes.decode()
        msg = str.split(data, SEP)
        seq_num_recv = msg[0]
        checksum = msg[1]
        packet_data = (msg[3]).encode()
        #random_number=random.uniform(0,1)
        random_number=1
        if (random_number <= probablity):
                print ("\nPacket Loss", (int(seq_num_recv,2)))  
        else:
            valid=check_checksum(packet_data, checksum)
            if (valid == 0):
                    if (seq_num_recv == '{0:032b}'.format(seq_num)):
                        ACKmsg = seq_num_recv+SEP+ACK_HEADER+SEP+ACK_INDICATOR
                        ServerSock.sendto(ACKmsg.encode(),client_address)
                        file_received.write(packet_data)
                        if msg[2] == DATA_INDICATOR_LAST:
                            file_received.close()
                            print ("\nFile has been transferred successfully!")
                            break
                        bytesReceived = len(msg[3])
                        seq_num += bytesReceived
                    else:
                        print ("\nReceived packet is out-of-order and sending previous ACK")
                        ACKmsg ='{0:032b}'.format(seq_num-bytesReceived)+SEP+ACK_HEADER+SEP+ACK_INDICATOR
                        ServerSock.sendto(ACKmsg,client_address)
            else:
                print("The checksum was invalid") 

if __name__ == '__main__':
    main()

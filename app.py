#!/usr/bin/env python3

import socket
import logging
import threading


def hello():

    # This is the IP address of the machine that the data will be send to
    UDP_IP = "138.38.228.111"

    UDP_PORT = 50001

    # This is the message. In this case it is a string
    MESSAGE = "Hello, World!"

    # Print the values for confirmation
    print("UDP target IP:", UDP_IP)
    print("UDP target port:", UDP_PORT)
    print("message:", MESSAGE)

    # Create the socket for the UDP communication
    sock = socket.socket(socket.AF_INET,    # Family of addresses, in this case IP type
                         socket.SOCK_DGRAM)  # What protocol to use, in this case UDP (datagram)

    # Send the message over the UDP socket. Not checking if it is done
    sock.sendto(bytearray(MESSAGE, 'utf-8'),  # You need this command bytearray to convert the string to Bytes (utf-8 = unit8)
                (UDP_IP, UDP_PORT))


hello()

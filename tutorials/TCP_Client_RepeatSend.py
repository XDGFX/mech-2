#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is an example to send data over a TCP connection to a Server.

@author: ioannisgeorgilas
"""

import socket
import time
import logging

# setting the logging level to INFO
logging.basicConfig(level=logging.INFO)

# This is the IP address of the machine that the data will be send to
TCP_IP = "192.168.0.220"

# This is the REMOTE port of the Server that we are sending the data to
TCP_PORT = 25000

# Create the socket for the UDP communication
s = socket.socket(socket.AF_INET,        # Family of addresses, in this case IP type
                  socket.SOCK_STREAM)    # What protocol to use, in this case TCP (streamed communications)
logging.info('Socket successfully created')

# Establish the connection with the remote Server using their IP and the port
s.connect((TCP_IP, TCP_PORT))
logging.info('Connected')

# We are going to send 3 bytes with values 50, 60, 70, ten times
data = bytes([50, 60, 70])

for i in range(0, 10):
    s.send(data)        # Send all 3 bytes in a go
    time.sleep(1)       # Wait for 1 second

# Close the connection
s.close()
logging.info('Done')

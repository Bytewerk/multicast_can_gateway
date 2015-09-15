#!/usr/bin/python3

__author__ = "Peter Brantsch"

import time
import socket

MCAST_ADDR = "224.0.0.1"
MCAST_PORT = 1337

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	while True:
		sock.sendto("Hello Multicast!".encode(), (MCAST_ADDR, MCAST_PORT))
		time.sleep(0.5)

if __name__ == '__main__':
	main()

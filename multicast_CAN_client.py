#!/usr/bin/python3

__author__ = "Peter Brantsch"

import socket
import struct

MCAST_ADDR = "224.0.0.1"
MCAST_PORT = 1338

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	mreq = struct.pack('4sL', socket.inet_aton(MCAST_ADDR), socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	#sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
	sock.bind(('', MCAST_PORT))
	while True:
		try:
			print(sock.recvfrom(16))
		except KeyboardInterrupt:
			raise
		except BaseException as e:
			print(e)

if __name__ == '__main__':
	main()

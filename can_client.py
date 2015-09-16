#!/usr/bin/python3

import socket
import time
import selectors

interface = 'can0'
RECONNECT_TIMEOUT = 10
SELECT_TIMEOUT = 1

def main():
	sel = selectors.DefaultSelector()
	while True:
		sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
		sock.bind((interface,))
		sel.register(sock, selectors.EVENT_READ)
		while True:
			events = sel.select(SELECT_TIMEOUT)
			for key, mask in events:
				print(key.fileobj.recv(1024))
		time.sleep(RECONNECT_TIMEOUT)


if __name__ == '__main__':
	main()

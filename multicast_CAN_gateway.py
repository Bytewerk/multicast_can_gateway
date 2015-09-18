#!/usr/bin/python3

__author__ = "Peter Brantsch"

import sys
import traceback
import time
import socket
import argparse
import selectors
import logging
import can

RECONNECT_TIMEOUT = 10
SELECT_TIMEOUT = 10

parser = argparse.ArgumentParser(description='Translate between UDP and CAN.')
parser.add_argument('--can-interface',\
		type=str,\
		default='can0',\
		help='the CAN interface to use')
parser.add_argument('--address',\
		type=str,\
		required=True,\
		help='the multicast address to send to')
parser.add_argument('--send-port',\
		type=int,\
		required=True,\
		help='the UDP multicast port to send to')
parser.add_argument('--recv-port',\
		type=int,\
		required=True,\
		help='the UDP unicast port to listen on')

logging.basicConfig(level=logging.DEBUG)

def main(args):
	"""
	Run the main loop of the gateway.
	"""
	logger = logging.getLogger("CAN-gateway")
	selector = selectors.DefaultSelector()
	while True:
		try:
			can_sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
			can_sock.bind((args.can_interface,))
			logger.debug("successfully created CAN socket %r",can_sock)
			def cbCANreadMsg():
				msgBytes = can_sock.recv(can.CANMessage.size)
				message = can.unpack(msgBytes)
				logger.debug("[-->] %r", message)
			selector.register(can_sock, selectors.EVENT_READ, cbCANreadMsg)

			mcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			logger.debug("sucessfully created multicast socket %r", mcast_sock)

			recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			recv_sock.bind(("", args.recv_port))
			logger.debug("successfully created receiving unicast socket %r", recv_sock)
			def cbRecvRead():
				msgBytes = recv_sock.recv(can.CANMessage.size)
				message = can.unpack(msgBytes)
				logger.debug("[<--] %r", message)
				can_sock.send(msgBytes)
			selector.register(recv_sock, selectors.EVENT_READ, cbRecvRead)

			while True:
				events = selector.select(SELECT_TIMEOUT)
				if not events:
					logger.debug("{}s passed without an event".format(SELECT_TIMEOUT))
				for key, mask in events:
					key.data()
		except Exception as ex:
			logger.exception(ex)
		time.sleep(RECONNECT_TIMEOUT)


if __name__ == '__main__':
	args = parser.parse_args()
	main(args)

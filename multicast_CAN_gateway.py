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
	canToudp_queue = []
	udpTocan_queue = []
	while True:
		try:
			can_sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
			can_sock.setblocking(False)
			can_sock.bind((args.can_interface,))
			logger.debug("successfully created CAN socket %r", can_sock)
			def cbCAN(mask):
				try:
					if mask & selectors.EVENT_READ:
						msgBytes = can_sock.recv(can.CANMessage.size)
						message = can.unpack(msgBytes)
						canToudp_queue.append(message)
						logger.debug("[CAN --> UDP] %r", message)
						selector.modify(udp_sock, selectors.EVENT_READ|selectors.EVENT_WRITE, cbUDP)
					if mask & selectors.EVENT_WRITE:
						if len(udpTocan_queue) > 0:
							msgBytes = udpTocan_queue.pop(0)
							can_sock.send(msgBytes)
						else:
							selector.modify(can_sock, selectors.EVENT_READ, cbCAN)
				except Exception as ex:
					logger.exception(ex)
			selector.register(can_sock, selectors.EVENT_READ, cbCAN)

			udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			udp_sock.setblocking(False)
			udp_sock.bind(("", args.recv_port))
			logger.debug("successfully created UDP socket %r", udp_sock)
			def cbUDP(mask):
				try:
					if mask & selectors.EVENT_READ:
						msgBytes = udp_sock.recv(can.CANMessage.size)
						udpTocan_queue.append(msgBytes)
						message = can.unpack(msgBytes)
						logger.debug("[CAN <-- UDP] %r", message)
						selector.modify(can_sock, selectors.EVENT_READ|selectors.EVENT_WRITE, cbCAN)
					if mask & selectors.EVENT_WRITE:
						if len(canToudp_queue) > 0:
							msgBytes = canToudp_queue.pop(0)
							udp_sock.sendTo(msgBytes, (args.address, args.send_port))
						else:
							selector.modify(udp_sock, selectors.EVENT_READ, cbUDP)
				except Exception as ex:
					logger.exception(ex)
			selector.register(udp_sock, selectors.EVENT_READ, cbUDP)

			while True:
				events = selector.select(SELECT_TIMEOUT)
				if not events:
					logger.debug("{}s passed without an event".format(SELECT_TIMEOUT))
				for key, mask in events:
					key.data(mask)
		except Exception as ex:
			logger.exception(ex)
		time.sleep(RECONNECT_TIMEOUT)


if __name__ == '__main__':
	args = parser.parse_args()
	main(args)

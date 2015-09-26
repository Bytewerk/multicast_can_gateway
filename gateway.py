#!/usr/bin/python3

__author__ = "Peter Brantsch"

import sys
import traceback
import time
import socket
import selectors
import logging
try:
	from . import can
except: # when running from command line, relative import will not work
	import can

logging.basicConfig(level=logging.DEBUG,\
		format='[%(asctime)-15s] %(module)-s: [%(levelname)-s] %(message)s')
logger = logging.getLogger(__name__)

class MulticastCANGateway():
	reconnectTimeout = 10
	selectTimeout = 10

	def __init__(self, canInterface, recvAddress=None, recvAddress6=None, mcastAddress=None, mcastAddress6=None):
		self.canInterface = canInterface
		self.mcastAddress = mcastAddress
		self.mcastAddress6 = mcastAddress6
		self.recvAddress = recvAddress
		self.recvAddress6 = recvAddress6
		self.canQueue = []
		self.udpQueue = []
		self.selector = selectors.DefaultSelector()
		self.sockCAN = None
		self.sockUDP = None
		self.sockUDP6 = None

	def __ensureCANsocket(self):
		""" Make sure there is a CAN socket. """
		if not self.sockCAN:
			self.sockCAN = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
			self.sockCAN.setblocking(False)
			self.sockCAN.bind(self.canInterface)
			self.selector.register(self.sockCAN, selectors.EVENT_READ, self.__do_CAN)
			logger.debug("successfully created CAN socket %r", self.sockCAN)

	def __ensureUDPsocket(self):
		""" Make sure there is a datagram socket. """
		if not self.sockUDP:
			self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.sockUDP.setblocking(False)
			self.sockUDP.bind(self.recvAddress)
			self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.selector.register(self.sockUDP, selectors.EVENT_READ, self.__do_UDP)
			logger.debug("successfully created UDP socket %r", self.sockUDP)

	def __ensureUDP6socket(self):
		""" Make sure there is an IPv6 datagram socket. """
		if not self.sockUDP6:
			self.sockUDP6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
			self.sockUDP6.setblocking(False)
			self.sockUDP6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sockUDP6.bind(self.recvAddress6)
			self.selector.register(self.sockUDP6, selectors.EVENT_READ, self.__do_UDP)
			logger.debug("successfully created IPv6 UDP socket %r", self.sockUDP)

	def __do_UDP(self, status):
		""" Perform UDP send/receive. """
		try:
			if status & selectors.EVENT_READ:
				msgBytes = self.sockUDP.recv(can.CANMessage.size)
				self.canQueue.append(msgBytes)
				message = can.unpack(msgBytes)
				logger.debug("[UDP --> CAN-queue] %r", message)
				self.selector.modify(self.sockCAN, selectors.EVENT_READ|selectors.EVENT_WRITE, self.__do_CAN)
			if status & selectors.EVENT_WRITE:
				if len(self.udpQueue) > 0:
					msgBytes = self.udpQueue.pop(0)
					message = can.unpack(msgBytes)
					self.sockUDP.sendto(msgBytes, self.mcastAddress)
					logger.debug("[UDP-queue --> UDP] %r", message)
				else:
					self.selector.modify(self.sockUDP, selectors.EVENT_READ, self.__do_UDP)
		except Exception as ex:
			logger.exception(ex)

	def __do_CAN(self, status):
		""" Perform CAN send/receive. """
		try:
			if status & selectors.EVENT_READ:
				msgBytes = self.sockCAN.recv(can.CANMessage.size)
				self.udpQueue.append(msgBytes)
				message = can.unpack(msgBytes)
				logger.debug("[CAN --> UDP-queue] %r", message)
				self.selector.modify(self.sockUDP, selectors.EVENT_READ|selectors.EVENT_WRITE, self.__do_UDP)
			if status & selectors.EVENT_WRITE:
				if len(self.canQueue) > 0:
					msgBytes = self.canQueue.pop(0)
					message = can.unpack(msgBytes)
					self.sockCAN.send(msgBytes)
					logger.debug("[CAN-queue --> CAN] %r", message)
				else:
					self.selector.modify(self.sockCAN, selectors.EVENT_READ, self.__do_CAN)
		except Exception as ex:
			logger.exception(ex)

	def run(self):
		""" Run the main loop. """
		while True:
			self.__ensureCANsocket()
			self.__ensureUDPsocket()
			self.__ensureUDP6socket()
			try:
				while True:
					events = self.selector.select(self.selectTimeout)
					if not events:
						logger.debug("{}s passed without an event".format(self.selectTimeout))
					for key, status in events:
						key.data(status)
			except Exception as ex:
				logger.exception(ex)
			time.sleep(self.reconnectTimeout)

def main(args):
	"""
	Run the main loop of the gateway.
	"""
	gateway = MulticastCANGateway((args.can_interface,),\
			mcastAddress = (args.address, args.send_port),\
			mcastAddress6 = (args.address6, args.send_port),\
			recvAddress = ("", args.recv_port),\
			recvAddress6 = ("", args.recv_port))
	gateway.run()

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Translate between UDP and CAN.')
	parser.add_argument('--can-interface',\
			type=str,\
			default='can0',\
			help='The CAN interface to use.')
	parser.add_argument('--address',\
			type=str,\
			#required=True,\
			help='The IPv4 multicast address to send to. At least one of --address6 or --address must be given.')
	parser.add_argument('--address6',\
			type=str,\
			help='The IPv6 multicast address to send to. At least one of --address6 or --address must be given.')
	parser.add_argument('--send-port',\
			type=int,\
			required=True,\
			help='The UDP multicast port to send to.')
	parser.add_argument('--recv-port',\
			type=int,\
			required=True,\
			help='The UDP unicast port to listen on.')
	args = parser.parse_args()
	if not (args.address or args.address6):
		parser.print_help()
		exit(2)
	main(args)

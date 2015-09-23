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

logging.basicConfig(level=logging.DEBUG,\
		format='[%(asctime)-15s] %(module)-s: [%(levelname)-s] %(message)s')
logger = logging.getLogger(__name__)

class MulticastCANGateway():
	reconnectTimeout = 10
	selectTimeout = 10

	def __init__(self, canInterface, mcastAddress, recvAddress):
		self.canInterface = canInterface
		self.mcastAddress = mcastAddress
		self.recvAddress = recvAddress
		self.canQueue = []
		self.udpQueue = []
		self.selector = selectors.DefaultSelector()
		self.sockCAN = None
		self.sockUDP = None

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
			self.selector.register(self.sockUDP, selectors.EVENT_READ, self.__do_UDP)
			logger.debug("successfully created UDP socket %r", self.sockUDP)

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
	gateway = MulticastCANGateway((args.can_interface,), (args.address, args.send_port), ("", args.recv_port))
	gateway.run()

if __name__ == '__main__':
	args = parser.parse_args()
	main(args)

#!/usr/bin/python3
"""
Receive CAN messages via UDP multicast, send CAN messages to server via UDP unicast.
"""

__author__ = "Peter Brantsch"

import socket
import logging
import struct
import ipaddress
from . import can

class MulticastCANClient():
    """
    The actual client class used to receive and send messages.
    """

    def __init__(self, mcastAddress, serverAddress):
        """
        Both *mcastAddress* and *serverAddress* must be 2-tuples of an
        ipaddress.IPv4Address or ipaddress.IPv6Address and the integer port
        number.
        """
        self.mcastAddress = mcastAddress
        if not mcastAddress[0].is_multicast:
            raise TypeError("mcastAddress must be a multicast address!")
        self.serverAddress = serverAddress
        if isinstance(mcastAddress[0], ipaddress.IPv6Address):
            self.sockUDP = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            mreq6 = struct.pack('16sI', self.mcastAddress[0].packed, socket.INADDR_ANY)
            #self.sockUDP.setsockopt(socket.IPPROTO_ICMPV6, socket.IPV6_MULTICAST_IF, 1)
            self.sockUDP.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq6)
        else:
            self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            mreq = struct.pack('4sL', self.mcastAddress[0].packed, socket.INADDR_ANY)
            self.sockUDP.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sockUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sockUDP.bind(('', self.mcastAddress[1]))

    def recvMsg(self):
        """
        Receive and return a CANMessage.
        """
        msgBytes, _ = self.sockUDP.recvfrom(can.CANMessage.size)
        msg = can.unpack(msgBytes)
        logger.debug("received: %r", msg)
        return msg

    def sendMsg(self, msg):
        """
        Send CANMessage *msg* to the server.
        """
        self.sockUDP.sendto(bytes(msg), self.serverAddress)
        logger.debug("sent: %r", msg)

def main(args):
    """
    Demo main function which just prints out received multicast packets.
    """
    client = MulticastCANClient((args.mcast_address, args.mcast_port), None)
    while True:
        client.recvMsg()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mcast-address', type=ipaddress.ip_address, required=True)
    parser.add_argument('--mcast-port', type=int, required=True)

    logging.basicConfig(level=logging.DEBUG,\
            format='[%(asctime)-15s] %(module)-s: [%(levelname)-s] %(message)s')
    logger = logging.getLogger(__name__)
    main(parser.parse_args())

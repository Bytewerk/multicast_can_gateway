"""
This module provides the *CANMessage* class which represents CAN-Bus messages
received or sent via socketcan.
"""

__author__ = "Peter Brantsch"

import struct

class CANMessage():
    """
    Instances of this class represent CAN-Bus messages sent or received via socketcan.
    """
    msg_fmt = "=IB3x8s"
    size = struct.calcsize(msg_fmt)

    def __init__(self, canid=0x0, data=b'', dlc=0):
        """
        Create a new message with the given *canid*, *data* and optional *dlc*.
        """
        self.canid = canid
        self.dlc = dlc if dlc else 0
        self.set_data(data)

    def set_data(self, data):
        """
        Set the *data* on this message.
        """
        data_len = len(data)
        if data_len > 8:
            raise ValueError("Data length is {} but must not be larger than 8".format(data_len))
        self.dlc = data_len
        self.data = data.ljust(8, b'\x00')

    def __bytes__(self):
        return struct.pack(self.msg_fmt, self.canid, self.dlc, self.data)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return type(self).__name__\
                + "(canid={0:x},dlc={1},data={2!r})".format(self.canid, self.dlc, self.data)

def unpack(msg_bytes):
    """
    Unpack *msg_bytes* into a CANMessage.
    """
    canid, dlc, data = struct.unpack(CANMessage.msg_fmt, msg_bytes)
    msg = CANMessage(canid, data, dlc)
    return msg

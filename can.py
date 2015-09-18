import struct

class CANMessage():
	msg_fmt = "=IB3x8s"
	size = struct.calcsize(msg_fmt)

	def __init__(self, canid=0x0, data=b''):
		self.canid = canid
		self.dlc = 0
		self.setData(data)

	def setData(self, data):
		self.dlc = len(data)
		self.data = data.ljust(8, b'\x00')

	def pack(self):
		return struct.pack(self.msg_fmt, self.canid, self.dlc, self.data)

	def __bytes__(self):
		return self.pack()

	def __str__(self):
		return repr(self)

	def __repr__(self):
		return "CANMessage(canid={0:x},dlc={1},data={2!r})".format(self.canid, self.dlc, self.data)

def unpack(msg_bytes):
	canid, dlc, data = struct.unpack(CANMessage.msg_fmt, msg_bytes)
	msg = CANMessage(canid, data)

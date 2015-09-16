import struct

class CANMessage():
	msg_fmt = "=IB3x8s"

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

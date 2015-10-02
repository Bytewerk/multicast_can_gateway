Multicast-CAN-Gateway
=====================

This project aims to provide a gateway between UDP multicast and socket-CAN.
Messages received via socket-CAN will be forwarded via UDP multicast.
Messages received via *unicast* will be forwarded via socket-CAN.

installation
------------

	python setup.py --install

Just use the Python setuptools the way you normally would.
There is nothing special to do yet.

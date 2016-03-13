#!/usr/bin/env python
#
#	Known bits Transmitter Script
#	Transmit a fixed packet repeatedly. Useful for BER testing.
#
#	Mark Jessop <vk5qi@rfhead.net>
#

import PacketTX,  sys, os, time
import numpy as np

payload = np.arange(0,256,1).astype(np.uint8).tostring() # 0->255

debug_output = False # If True, packet bits are saved to debug.bin as one char per bit.


tx = PacketTX.PacketTX(debug=debug_output)
tx.start_tx()

try:
	while True:
		tx.tx_packet(payload)
except KeyboardInterrupt:
	tx.close()
	print("Closing")

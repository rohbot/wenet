#!/usr/bin/env python
#
#	Test Transmitter Script
#	Transmit a set of images from the test_images directory
#
#	Mark Jessop <vk5qi@rfhead.net>
#

import PacketTX,  sys, os

# Set to whatever resolution you want to test.
file_path = "../test_images/%d_raw.ssdv" # _raw, _800x608, _640x480, _320x240
image_numbers = xrange(1,14)

debug_output = False # If True, packet bits are saved to debug.bin as one char per bit.

def transmit_file(filename, tx_object):
	file_size = os.path.getsize(filename)

	if file_size % 256 > 0:
		print("File size not a multiple of 256 bytes!")
		return

	print("Transmitting %d Packets." % (file_size/256))

	f = open(filename,'rb')

	for x in range(file_size/256):
		data = f.read(256)
		tx_object.tx_packet(data)

	f.close()
	print("Waiting for tx queue to empty...")
	tx_object.wait()


tx = PacketTX.PacketTX(debug=debug_output)
tx.start_tx()
print("TX Started. Press Ctrl-C to stop.")
try:
	for img in image_numbers:
		filename = file_path % img
		print("\nTXing: %s" % filename)
		transmit_file(filename,tx)
	tx.close()
except KeyboardInterrupt:
	print("Closing...")
	tx.close()

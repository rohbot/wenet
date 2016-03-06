#!/usr/bin/env python
#
#	Receiver Test Script.
#	Feeds a list of test images into the receiver code, via stdout/stdin.
#
#	Mark Jessop <vk5qi@rfhead.net>
#

import time, sys, os

# Set to whatever resolution you want to test.
file_path = "./test_images/%d_raw.ssdv" # _raw, _800x608, _640x480, _320x240
image_numbers = xrange(1,14)

print_as_hex = False

delay_time = 0.0239 # Approx time for one 256 byte packet at 115.2k baud

def print_file(filename):
	file_size = os.path.getsize(filename)

	if file_size % 256 > 0:
		return

	f = open(filename,'rb')

	for x in range(file_size/256):
		data = f.read(256)
		if print_as_hex:
			data = "".join("{:02x}".format(ord(c)) for c in data) + "\n"

		sys.stdout.write(data)
		sys.stdout.flush()
		time.sleep(delay_time)

	f.close()

for img in image_numbers:
	filename = file_path % img
	print_file(filename)

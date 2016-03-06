#!/usr/bin/env python
#
#	PiCam Transmitter Script
#	Capture images from the PiCam, and transmit them,
#
#	Mark Jessop <vk5qi@rfhead.net>
#

import PacketTX,  sys, os

# Set to whatever resolution you want to transmit.
tx_resolution = "1024x768"
callsign = "VK5QI"


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

image_id = 0

try:
	while True:
		# Capture image using PiCam
		print("Capturing Image...")
		os.system("raspistill -t 100 -o temp.jpg -vf -hf -w 1024 -h 768")
		# Resize using convert
		print("Processing...")
		#os.system("convert temp.jpg -resize %s\! temp.jpg" % tx_resolution)
		# SSDV'ify the image.
		os.system("ssdv -e -c %s -i %d temp.jpg temp.ssdv" % (callsign,image_id))
		# Transmit image
		print("Transmitting...")
		transmit_file("temp.ssdv",tx)

		# Increment Counter
		image_id = (image_id+1)%256
except KeyboardInterrupt:
	print("Closing")
	tx.close()

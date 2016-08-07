#!/usr/bin/env python
#
#	PiCam Transmitter Script
#	Capture images from the PiCam, and transmit them.
#
#	Mark Jessop <vk5qi@rfhead.net>
#

import PacketTX,  sys, os, datetime
from picam_wrapper import *

try:
	callsign = sys.argv[1]
	if len(callsign)>6:
		callsign = callsign[:6]
except:
	print("Usage: python tx_picam.py CALLSIGN")
	sys.exit(1)

print("Using callsign: %s" % callsign)


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
		capture_time = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")
		capture_multiple(filename="./tx_images/%s.jpg"%capture_time)
		#os.system("raspistill -t 100 -o ./tx_images/%s.jpg -vf -hf -w 1024 -h 768" % capture_time)
		# Resize using convert
		print("Processing...")
		#os.system("convert temp.jpg -resize %s\! temp.jpg" % tx_resolution)
		# SSDV'ify the image.
		os.system("ssdv -e -n -c %s -i %d ./tx_images/%s.jpg temp.ssdv" % (callsign,image_id,capture_time))
		# Transmit image
		print("Transmitting...")
		transmit_file("temp.ssdv",tx)

		# Increment Counter
		image_id = (image_id+1)%256
except KeyboardInterrupt:
	print("Closing")
	tx.close()

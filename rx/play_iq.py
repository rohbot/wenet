#!/usr/bin/env python
#
#	IQ Test Script
#	
#	Play back an IQ file at a user-supplied rate. 
#	IQ file must be in 8-bit complex format (i.e. the output from rtl_sdr)
#
#	Run using: 
#		python play_iq.py ../test_iq/test_images.bin 1000000 | ./fsk_demod --cu8 -s 2 921416 115177 - - | ./drs232_ldpc - - -vv | python rx_ssdv.py --partialupdate 16
#
#	Copyright (C) 2019  Mark Jessop <vk5qi@rfhead.net>
#	Released under GNU GPL v3 or later
#

import sys
import time

# Check if we are running in Python 2 or 3
PY3 = sys.version_info[0] == 3

filename = sys.argv[1]
rate = int(sys.argv[2])

with open(filename,'rb') as in_file:
	while True:
		# Read in N samples from the file.
		data = in_file.read(rate*2)

		if PY3:
			sys.stdout.buffer.write(data)
		else:
			sys.stdout.write(data)

		sys.stdout.flush()
		time.sleep(1)

#!/bin/bash
#
#	Wenet TX-side Initialisation Script
#	2016-08-07 Mark Jessop <vk5qi@rfhead.net>
#
#	Run this to set up an attached RFM22B and start transmitting!
#	Replace the transmit frequency and callsign with your own.
#
python init_rfm22b.py 441.200
python tx_picam.py VK5QI &

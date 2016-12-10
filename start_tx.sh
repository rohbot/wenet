#!/bin/bash
#
#	Wenet TX-side Initialisation Script
#	2016-12-05 Mark Jessop <vk5qi@rfhead.net>
#
#	Run this to set up an attached RFM22B/RFM98W and start transmitting!
#	Replace the transmit frequency and callsign with your own.
#

MYCALL=N0CALL
TXFREQ=441.200

# CHANGE THE FOLLOWING LINE TO REFLECT THE ACTUAL PATH TO THE TX FOLDER.
# i.e. it may be /home/username/dev/wenet/tx/
cd ~/wenet/tx/

#Uncomment to initialise a RFM22B
#python init_rfm22b.py $TXFREQ
# Uncomment for use with a RFM98W
python init_rfm98w.py $TXFREQ

# Start the main TX Script.
# Note, this assumes there is a uBlox GPS available at /dev/ttyACM0
python tx_picam_gps.py $MYCALL &

# If you don't want any GPS overlays, you can comment the above line and run:
# python WenetPiCam.py $MYCALL &
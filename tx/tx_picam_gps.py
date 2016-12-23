#!/usr/bin/env python
#
#	PiCam Transmitter Script - with GPS Data and Logo Overlay.
#	Capture images from the PiCam, and transmit them.
#
#	Mark Jessop <vk5qi@rfhead.net>
#

import PacketTX
import WenetPiCam
import ublox
import argparse
import time
import os

parser = argparse.ArgumentParser()
parser.add_argument("callsign", default="N0CALL", help="Payload Callsign")
parser.add_argument("--gps", default="/dev/ttyACM0", help="uBlox GPS Serial port. Defaults to /dev/ttyACM0")
parser.add_argument("--logo", default="none", help="Optional logo to overlay on image.")
parser.add_argument("--txport", default="/dev/ttyAMA0", type=str, help="Transmitter serial port. Defaults to /dev/ttyAMA0")
parser.add_argument("--baudrate", default=115200, type=int, help="Transmitter baud rate. Defaults to 115200 baud.")
args = parser.parse_args()

callsign = args.callsign
# Truncate callsign if it's too long.
if len(callsign) > 6:
	callsign = callsign[:6]

print("Using Callsign: %s" % callsign)


# Start up Wenet TX.
tx = PacketTX.PacketTX(serial_port=args.txport, serial_baud=args.baudrate, callsign=callsign)
tx.start_tx()

# Sleep for a second to let the transmitter fire up.
time.sleep(1)

# Initialise a couple of global variables.
max_altitude = 0

def handle_gps_data(gps_data):
	""" Handle GPS data passed to us from the UBloxGPS instance """
	global max_altitude, tx

	# Immediately transmit a GPS packet.
	tx.transmit_gps_telemetry(gps_data)

	if gps_data['altitude'] > max_altitude:
		max_altitude = gps_data['altitude']


# Try and start up the GPS rx thread.
try:
	gps = ublox.UBloxGPS(port=args.gps, 
		dynamic_model = ublox.DYNAMIC_MODEL_AIRBORNE1G, 
		update_rate_ms = 1000,
		debug_ptr = tx.transmit_text_message,
		callback = handle_gps_data,
		log_file = 'gps_data.log'
		)
except Exception as e:
	tx.transmit_text_message("ERROR: Could not Open GPS - %s" % str(e), repeats=5)
	gps = None

# Define our post-processing callback function, which gets called by WenetPiCam
# after an image has been captured.
def post_process_image(filename):
	""" Post-process the image, adding on Logo overlay and GPS data if requested. """
	global gps, max_altitude, args, tx

	# Try and grab current GPS data snapshot
	if gps != None:
		gps_state = gps.read_state()

		# Send GPS telemetry packet here.

		# Construct string which we will add onto the image.
		if gps_state['numSV'] < 3:
			# If we don't have enough sats for a lock, don't display any data.
			# TODO: Use the GPS fix status values here instead.
			gps_string = "No GPS Lock"
		else:
			gps_string = "Lat: %.5f   Lon: %.5f  Alt: %dm (%dm)  Speed: H %03.1f kph  V %02.1f m/s" % (gps_state['latitude'],
				gps_state['longitude'],
				int(gps_state['altitude']),
				int(max_altitude),
				gps_state['ground_speed'],
				gps_state['ascent_rate'])
	else:
		gps_string = "No GPS"

	# Build up our imagemagick 'convert' command line
	overlay_str = "convert %s -gamma 0.8 -font Helvetica -pointsize 30 -gravity North " % filename 
	overlay_str += "-strokewidth 2 -stroke '#000C' -annotate +0+5 \"%s\" " % gps_string
	overlay_str += "-stroke none -fill white -annotate +0+5 \"%s\" " % gps_string
	# Add on logo overlay argument if we have been given one.
	if args.logo != "none":
		overlay_str += "%s -gravity SouthEast -composite " % args.logo

	overlay_str += filename

	tx.transmit_text_message("Adding overlays to image.")
	os.system(overlay_str)

	return


# Finally, initialise the PiCam capture object.
picam = WenetPiCam.WenetPiCam(resolution=(1920,1088), callsign=callsign, debug_ptr=tx.transmit_text_message, vertical_flip=True, horizontal_flip=True)
# .. and start it capturing continuously.
picam.run(destination_directory="./tx_images/", 
	tx = tx,
	post_process_ptr = post_process_image
	)


# Main 'loop'.
try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	print("Closing")
	picam.stop()
	tx.close()
	gps.close()

















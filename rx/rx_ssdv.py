#!/usr/bin/env python
#
#	SSDV Packet Receiver & Parser
#	Decodes SSDV packets passed via stdin.
#
#	Copyright (C) 2018  Mark Jessop <vk5qi@rfhead.net>
#	Released under GNU GPL v3 or later
#
#	Requires: ssdv (https://github.com/fsphil/ssdv)
#

import json
import os
import sys
import datetime
import argparse
import socket
from WenetPackets import *

parser = argparse.ArgumentParser()
parser.add_argument("--hex", action="store_true", help="Take Hex strings as input instead of raw data.")
parser.add_argument("--partialupdate",default=0,help="Push partial updates every N packets to GUI.")
args = parser.parse_args()


# GUI updates are only sent locally.
def trigger_gui_update(filename, text = "None"):
	message = 	{'filename': filename,
				'text': text}

	gui_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	gui_socket.sendto(json.dumps(message),("127.0.0.1",WENET_IMAGE_UDP_PORT))
	gui_socket.close()

# Telemetry packets are send via UDP broadcast in case there is other software on the local
# network that wants them.
def broadcast_telemetry_packet(data):
	telemetry_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	# Set up the telemetry socket so it can be re-used.
	telemetry_socket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
	telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	# We need the following if running on OSX.
	try:
		telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
	except:
		pass

	# Place data into dictionary.
	data = {'type': 'WENET', 'packet': list(bytearray(data))}

	# Send to broadcast if we can.
	try:
		telemetry_socket.sendto(json.dumps(data), ('<broadcast>', WENET_TELEMETRY_UDP_PORT))
	except socket.error:
		telemetry_socket.sendto(json.dumps(data), ('127.0.0.1', WENET_TELEMETRY_UDP_PORT))

	telemetry_socket.close()

# State variables
current_image = -1
current_callsign = ""
current_text_message = -1
current_packet_count = 0
current_packet_time = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")

# Open temporary file for storing data.
temp_f = open("rxtemp.bin",'wb')


while True:
	if args.hex:
		data = sys.stdin.readline().rstrip().decode('hex')
	else:
		data = sys.stdin.read(256)

	packet_type = decode_packet_type(data)


	if packet_type == WENET_PACKET_TYPES.IDLE:
		continue
	elif packet_type == WENET_PACKET_TYPES.TEXT_MESSAGE:
		broadcast_telemetry_packet(data)
		print(packet_to_string(data))

	elif packet_type == WENET_PACKET_TYPES.SEC_PAYLOAD_TELEMETRY:
		broadcast_telemetry_packet(data)
		print(packet_to_string(data))

	elif packet_type == WENET_PACKET_TYPES.GPS_TELEMETRY:
		broadcast_telemetry_packet(data)
		print(packet_to_string(data))

	elif packet_type == WENET_PACKET_TYPES.ORIENTATION_TELEMETRY:
		broadcast_telemetry_packet(data)
		print(packet_to_string(data))

	elif packet_type == WENET_PACKET_TYPES.IMAGE_TELEMETRY:
		broadcast_telemetry_packet(data)
		print(packet_to_string(data))

	elif packet_type == WENET_PACKET_TYPES.SSDV:

		# Extract packet information.
		packet_info = ssdv_packet_info(data)
		packet_as_string = ssdv_packet_string(data)

		# Only proceed if there are no decode errors.
		if packet_info['error'] != 'None':
			print(message['error'])
			continue

		if (packet_info['image_id'] != current_image) or (packet_info['callsign'] != current_callsign) :
			# Attempt to decode current image if we have enough packets.
			print("New image!")
			if current_packet_count > 0:
				# Attempt to decode current image, and write out to a file.
				temp_f.close()
				# Run SSDV
				returncode = os.system("ssdv -d rxtemp.bin ./rx_images/%s_%s_%d.jpg" % (current_packet_time,current_callsign,current_image))
				if returncode == 1:
					print("ERROR: SSDV Decode failed!")
				else:
					print("SSDV Decoded OK!")
					# Make a copy of the raw binary data.
					os.system("mv rxtemp.bin ./rx_images/%s_%s_%d.bin" % (current_packet_time,current_callsign,current_image))

					# Update live displays here.
					trigger_gui_update("./rx_images/%s_%s_%d.jpg" % (current_packet_time,current_callsign,current_image), packet_as_string)

					# Trigger upload to habhub here.
			else:
				print("Not enough packets to decode previous image.")

			# Now set up for the new image.
			current_image = packet_info['image_id']
			current_callsign = packet_info['callsign']
			current_packet_count = 1
			current_packet_time = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")
			# Open file and write in first packet.
			temp_f = open("rxtemp.bin" , "wb")
			temp_f.write(data)

		else:
			# Write current packet into temp file.
			temp_f.write(data)
			current_packet_count += 1

			if args.partialupdate != 0:
				if current_packet_count % int(args.partialupdate) == 0:
					# Run the SSDV decoder and push a partial update to the GUI.
					temp_f.flush()
					returncode = os.system("ssdv -d rxtemp.bin rxtemp.jpg")
					if returncode == 0:
						trigger_gui_update("rxtemp.jpg", packet_as_string)
	else:
		print("Unknown Packet Format.")
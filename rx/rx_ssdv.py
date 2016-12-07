#!/usr/bin/env python
#
#	SSDV Packet Receiver & Parser
#	Decodes SSDV packets passed via stdin.
#
#	Mark Jessop <vk5qi@rfhead.net>
#
#	Requires: ssdv (https://github.com/fsphil/ssdv)
#


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



# Helper functions to extract data from SSDV packets.

def ssdv_packet_info(packet):
	packet = list(bytearray(packet))
	# Check packet is actually a SSDV packet.
	if len(packet) != 256:
		return {'error': "ERROR: Invalid Packet Length"}

	if packet[0] != 0x55: # A first byte of 0x55 indicates a SSDV packet.
		if packet[0] == 0x00: # Interim arbitrary text message packet.
			print("%s \tText Message: %s" % (datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S.%fZ"),str(data)))
		else:
			print("%s \tUnknown packet type." % (datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S.%fZ")))
		return {'error': "ERROR: Not a SSDV Packet."}

	# We got this far, may as well try and extract the packet info.
	try:
		packet_info = {
			'callsign' : "???", # TODO: Callsign decoding.
			'packet_type' : "FEC" if (packet[1]==0x66) else "No-FEC",
			'image_id' : packet[6],
			'packet_id' : (packet[7]<<8) + packet[8],
			'width' : packet[9]*16,
			'height' : packet[10]*16,
			'error' : "None"
		}

		return packet_info
	except Exception as e:
		return {'error': "ERROR: %s" % str(e)}


def ssdv_packet_string(packet_info):
	return "%s \tSSDV: %s, Img:%d, Pkt:%d, %dx%d" % (datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S.%fZ"), packet_info['packet_type'],packet_info['image_id'],packet_info['packet_id'],packet_info['width'],packet_info['height'])


# GUI updates are only sent locally.
def trigger_gui_update(filename):
	gui_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	gui_socket.sendto(filename,("127.0.0.1",WENET_IMAGE_UDP_PORT))
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

    # Send to broadcast if we can.
    try:
        telemetry_socket.sendto(json.dumps(data), ('<broadcast>', WENET_TELEMETRY_UDP_PORT))
    except socket.error:
        telemetry_socket.sendto(json.dumps(data), ('127.0.0.1', WENET_TELEMETRY_UDP_PORT))

	telemetry_socket.close()

# State variables
current_image = -1
current_packet_count = 0
current_packet_time = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")

# Open temporary file for storing data.
temp_f = open("rxtemp.bin",'wb')

while True:
	if args.hex:
		data = sys.stdin.readline().rstrip().decode('hex')
	else:
		data = sys.stdin.read(256)

	packet_info = ssdv_packet_info(data)

	# Don't continue if we have a decode error.
	if packet_info['error'] != "None":
		continue

	print(ssdv_packet_string(packet_info))

	if packet_info['image_id'] != current_image:
		# Attempt to decode current image if we have enough packets.
		print("New image!")
		if current_packet_count > 0:
			# Attempt to decode current image, and write out to a file.
			temp_f.close()
			# Run SSDV
			returncode = os.system("ssdv -d rxtemp.bin ./rx_images/%s_%d.jpg" % (current_packet_time,current_image))
			if returncode == 1:
				print("ERROR: SSDV Decode failed!")
			else:
				print("SSDV Decoded OK!")
				# Make a copy of the raw binary data.
				os.system("mv rxtemp.bin ./rx_images/%s_%d.bin" % (current_packet_time,current_image))

				# Update live displays here.
				trigger_gui_update("./rx_images/%s_%d.jpg" % (current_packet_time,current_image))

				# Trigger upload to habhub here.
		else:
			print("Not enough packets to decode previous image.")

		# Now set up for the new image.
		current_image = packet_info['image_id']
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
					trigger_gui_update("rxtemp.jpg")


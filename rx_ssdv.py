#!/usr/bin/env python
#
#	SSDV Packet Receiver & Parser
#	Decodes SSDV packets passed via stdin.
#
#	Mark Jessop <vk5qi@rfhead.net>
#
#	Requires: ssdv (https://github.com/fsphil/ssdv)
#


import os,sys, datetime, argparse

parser = argparse.ArgumentParser()
parser.add_argument("--hex", action="store_true", help="Take Hex strings as input instead of raw data.")
args = parser.parse_args()

# Helper functions to extract data from SSDV packets.

def ssdv_packet_info(packet):
	packet = list(bytearray(packet))
	# Check packet is actually a SSDV packet.
	if len(packet) != 256:
		return {'error': "ERROR: Invalid Packet Length"}

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
	return "SSDV: %s, Img:%d, Pkt:%d, %dx%d" % (packet_info['packet_type'],packet_info['image_id'],packet_info['packet_id'],packet_info['width'],packet_info['height'])


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
			returncode = os.system("ssdv -d rxtemp.bin %s.jpg" % current_packet_time)
			if returncode == 1:
				print("ERROR: SSDV Decode failed!")
			else:
				print("SSDV Decoded OK!")
				# Make a copy of the raw binary data.
				os.system("mv rxtemp.bin %s.ssdv" % current_packet_time)

				# Update live displays here.

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


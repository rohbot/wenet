#!/usr/bin/env python2.7
#
#	SSDV Upload Library
#
#

import base64, requests, datetime, os

ssdv_url = "http://ssdv.habhub.org/api/v0/packets"

def ssdv_encode_packet(packet,callsign="N0CALL"):
	packet_dict = {
		"type":"packet",
		"packet":base64.b64encode(packet),
		"encoding":"base64",
		# Because .isoformat() doesnt give us the right format... (boo)
		"received":datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
		"receiver":callsign,
	}
	return packet_dict

def ssdv_upload_single(packet,callsign="N0CALL"):
	packet_dict = ssdv_encode_single(packet,callsign)

	r = requests.post(ssdv_url,json=packet_dict)
	return r

def ssdv_upload_multiple(packet_array,callsign="N0CALL"):
	encoded_array = []

	for packet in packet_array:
		encoded_array.append(ssdv_encode_packet(packet,callsign))

	packet_dict = {
		"type": "packets",
		"packets": encoded_array
	}
	r = requests.post(ssdv_url,json=packet_dict)
	return r


def ssdv_upload_file(filename,callsign="N0CALL", blocksize=16):
	file_size = os.path.getsize(filename)

	if file_size % 256 > 0:
		print("File size not a multiple of 256 bytes!")
		return

	packet_count = file_size/256
	print("Uploading %d packets." % packet_count)

	f = open(filename,"rb")

	while packet_count > 0:

		if packet_count <=blocksize:
			# Read and transmit remainder of file.
			data = f.read()
			packet_array = [ data[i:i+256] for i in range(0,len(data),256)]
			ssdv_upload_multiple(packet_array,callsign)
			packet_count = 0
		else:
			data = f.read(blocksize*256)
			packet_array = [ data[i:i+256] for i in range(0,len(data),256)]
			ssdv_upload_multiple(packet_array,callsign)
			packet_count = packet_count - blocksize

		print("%d packets remaining." % packet_count)

	f.close()

if __name__ == '__main__':
	import sys
	filename = sys.argv[1]
	callsign = sys.argv[2]
	print("Uploading: %s with Callsign: %s" % (filename,callsign))

	ssdv_upload_file(filename,callsign=callsign,blocksize=256)
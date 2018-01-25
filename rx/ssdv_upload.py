#!/usr/bin/env python2.7
#
#	Wenet SSDV Upload Script.
#
#	Copyright (C) 2018  Mark Jessop <vk5qi@rfhead.net>
#	Released under GNU GPL v3 or later
#
#	Watches the rx_images directory for new images, and uploads the latest image it sees.
#
#

import base64, requests, datetime, os, glob, time, traceback

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
	try:
		r = requests.post(ssdv_url,json=packet_dict)
	except Exception as e:
		print(e.strerror)
	return r


def ssdv_upload_file(filename,callsign="N0CALL", blocksize=16):
	file_size = os.path.getsize(filename)

	if file_size % 256 > 0:
		print("File size not a multiple of 256 bytes!")
		return

	packet_count = file_size/256
	print("Uploading %d packets." % packet_count)
	start_time = datetime.datetime.now()

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
	stop_time = datetime.datetime.now()
	upload_time = (stop_time-start_time).total_seconds()
	print("Upload Completed in %.2f Seconds." % upload_time)

def ssdv_dir_watcher(glob_string="./rx_images/*.bin", check_time = 0.5, callsign="N0CALL"):
	# Check what's there now..
	rx_images = glob.glob(glob_string)
	print("Starting directory watch...")

	while True:
		try:
			time.sleep(check_time)

			# Check directory again.
			rx_images_temp = glob.glob(glob_string)
			if len(rx_images_temp) == 0:
				continue
			# Sort list. Image filenames are timestamps, so the last element in the array will be the latest image.
			rx_images_temp.sort()
			# Is there an new image?
			if rx_images_temp[-1] not in rx_images:
				# New image! Wait a little bit in case we're still writing to that file, then upload.
				time.sleep(0.5)
				filename = rx_images_temp[-1]
				print("Found new image! Uploading: %s " % filename)
				ssdv_upload_file(filename,callsign=callsign,blocksize=256)

			rx_images = rx_images_temp
		except KeyboardInterrupt:
			sys.exit(0)
		except:
			traceback.print_exc()
			continue




if __name__ == '__main__':
	import sys
	try:
		callsign = sys.argv[1]
		if len(callsign)>6:
			callsign = callsign[:6]
	except:
		print("Usage: python ssdv_upload.py CALLSIGN &")
		sys.exit(1)

	print("Using callsign: %s" % callsign)


	ssdv_dir_watcher(callsign=callsign)

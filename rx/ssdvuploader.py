#!/usr/bin/env python
#
#	Wenet SSDV Upload Class
#
#	Copyright (C) 2019  Mark Jessop <vk5qi@rfhead.net>
#	Released under GNU GPL v3 or later
#
#	Somewhat more robust SSDV Uploader class, which can be instantiated from within 
#	another application and monitored.
#

import requests
import datetime
import logging
import os
import glob
import sys
import time
import traceback
from base64 import b64encode
from threading import Thread, Lock
try:
    # Python 2
    from Queue import Queue
except ImportError:
    # Python 3
    from queue import Queue


class SSDVUploader(object):
	"""
	Queued SSDV Imagery Uploader Class

	Based on the Queued habitat uploader class from auto_rx.

	"""


	SSDV_URL = "http://ssdv.habhub.org/api/v0/packets"

	def __init__(self,
		uploader_callsign = "N0CALL",
		enable_file_watch = True,
		watch_directory = "./rx_images/",
		file_mask = "*.bin",
		queue_size = 8192,
		upload_block_size = 256,
		upload_timeout = 10,
		upload_retries = 2,
		upload_anyway = 10
		):
		"""
		Initialise a SSDV Uploader Object
		
		Args:


			upload_retries (int): How many times to retry an upload on a timeout before discarding.


		"""

		self.uploader_callsign = uploader_callsign
		self.upload_block_size = upload_block_size
		self.upload_timeout = upload_timeout
		self.upload_retries = upload_retries
		self.upload_anyway = upload_anyway

		# Generate search mask.
		self.search_mask = os.path.join(watch_directory, file_mask)

		# Set up Queue
		self.upload_queue = Queue(queue_size)

		# Count of uploaded packets.
		self.upload_count = 0
		# Count of discarded packets due to upload failures.
		self.discard_count = 0


		# Start uploader and file watcher threads.
		self.uploader_running = True

		self.uploader_thread = Thread(target=self.uploader_loop)
		self.uploader_thread.start()

		if enable_file_watch:
			self.file_watch_thread = Thread(target=self.file_watch_loop)
			self.file_watch_thread.start()



	def ssdv_encode_packet(self, packet):
		''' Convert a packet to a suitable JSON blob. '''
		_packet_dict = {
			"type" :	"packet",
			"packet" :	b64encode(packet), # Note - b64encode accepts bytes objects under Python 3, and strings under Python 2.
			"encoding":	"base64",
			# Because .isoformat() doesnt give us the right format... (boo)
			"received":	datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
			"receiver":	self.uploader_callsign,
		}

		return _packet_dict


	def ssdv_upload_single(self, packet):
		_packet_dict = self.ssdv_encode_packet(packet,callsign)

		_attempts = 1
		while _attempts <= self.upload_retries:
			try:
				_r = requests.post(self.SSDV_URL, json=_packet_dict, timeout=self.upload_timeout)
				return True

			except requests.exceptions.Timeout:
				# Timeout! We can re-try.
				_attempts += 1
				continue

			except Exception as e:
				logging.error("Uploader - Error when uploading: %s" % str(e))
				break

		return False


	def ssdv_upload_multiple(self, count):
		# Sanity check that there are enough packet in the queue to upload.
		if count > self.upload_queue.qsize():
			count = self.upload_queue.qsize()

		_encoded_array = []

		for i in range(count):
			_encoded_array.append(self.ssdv_encode_packet(self.upload_queue.get()))

		_packet_dict = {
			"type": "packets",
			"packets": _encoded_array
		}

		_attempts = 1
		while _attempts <= self.upload_retries:
			try:
				_r = requests.post(self.SSDV_URL, json=_packet_dict, timeout=self.upload_timeout)
				logging.debug("Uploader - Successfuly uploaded %d packets." % count)
				return True

			except requests.exceptions.Timeout:
				# Timeout! We can re-try.
				_attempts += 1
				continue

			except Exception as e:
				logging.error("Uploader - Error when uploading: %s" % str(e))
				break

		return False


	def uploader_loop(self):
		logging.info("Started uploader thread.")


		_last_upload_time = time.time()

		while self.uploader_running:

			if self.upload_queue.qsize() >= self.upload_block_size:

				if self.ssdv_upload_multiple(self.upload_block_size):
					# Upload successful!
					self.upload_count += self.upload_block_size
				else:
					# The upload has failed, 
					self.discard_count += self.upload_block_size

				_last_upload_time = time.time()

			elif (self.upload_queue.qsize() > 0) and ( (time.time() - _last_upload_time) > self.upload_anyway):
				# We have some packets in the queue, and haven't uploaded in a while. Upload them.
				_packet_count = self.upload_queue.qsize()

				if self.ssdv_upload_multiple(_packet_count):
					# Upload successful!
					self.upload_count += _packet_count
				else:
					# The upload has failed, 
					self.discard_count += _packet_count

				_last_upload_time = time.time()

			time.sleep(1)


		logging.info("Closed uploader thread.")



	def file_watch_loop(self):
		logging.info("Started File Watcher Thread.")

		while self.uploader_running:

			# File watcher stuff here.

			time.sleep(1)


		logging.info("Closed File Watch Thread.")


	def get_queue_size(self):
		""" Return the packets remaining in the queue """
		return self.upload_queue.qsize()


	def get_upload_count(self):
		""" Return the total number of packets uploaded so far """
		return self.upload_count


	def add_packet(self, data):
		""" Add a single packet to the uploader queue. 
			If the queue is full, the packet will be immediately discarded.

			Under Python 2, this function should be passed strings.
			Under Python 3, it should be passed bytes objects.
		"""
		if len(data) == 256:
			try:
				self.upload_queue.put_nowait(data)
				return True
			except:
				# Queue was full.
				self.discard_count += 1
				if self.discard_count % 256 == 0:
					logging.warning("Upload Queue Full - Packets are being dropped.")
				return False


	def add_file(self, filename):
		""" Attempt to add a file to the upload queue """

		_file_size = os.path.getsize(filename)

		if _file_size%256 != 0:
			logging.error("%s size (%d) not a multiple of 256, likely not a SSDV file." % (filename, _file_size))
			return False

		_packet_count = _file_size / 256
		_packets_added = 0

		_f = open(filename, 'rb')

		for _i in range(_packet_count):
			_packet = _f.read(256)

			if self.add_packet(_packet):
				_packets_added += 1

		_f.close()

		logging.info("Added %d packets to queue." % _packets_added)


	def close(self):
		""" Stop uploader thread. """
		logging.info("Shutting down threads.")
		self.uploader_running = False





if __name__ == "__main__":

	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)

	if len(sys.argv) == 1:
		print("Usage: python ssdvuploader.py YOUR_CALLSIGN_HERE")
		sys.exit(1)
	else:
		_callsign = sys.argv[1]
		_uploader = SSDVUploader(uploader_callsign=_callsign)

	try:
		while True:
			time.sleep(5)
			print("%d packets in uploader queue. %d packets uploaded." % (_uploader.get_queue_size(), _uploader.get_upload_count()))
	except KeyboardInterrupt:
		_uploader.close()


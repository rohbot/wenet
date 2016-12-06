#!/usr/bin/env python2.7
#
#	Wenet PiCam Wrapper Class.
#
#

from picamera import PiCamera
from time import sleep
from threading import Thread
import glob
import os


class WenetPiCam(object):
	""" PiCam Wrapper Class

	PiCam Image Source for Wenet.
	Captures multiple images, picks the best, then 
	transmits it via a PacketTX object. 

	"""

	def __init__(self,resolution=(1488,1120), 
				num_images=5, 
				vertical_flip = False, 
				horizontal_flip = False,
				temp_filename_prefix = 'picam_temp',
				debug_ptr = None):

		self.debug_ptr = debug_ptr
		self.temp_filename_prefix = temp_filename_prefix
		self.num_images = num_images

		# Attempt to start picam.
		self.cam = PiCamera()

		# Configure camera.
		self.cam.resolution = resolution
		self.cam.hflip = horizontal_flip
		self.cam.vflip = vertical_flip
		self.cam.exposure_mode = 'auto'
		self.cam.awb_mode = 'auto'
		self.cam.meter_mode = 'matrix'

		# Start the 'preview' mode, effectively opening the 'shutter'.
		# This lets the camera gain control algs start to settle.
		self.cam.start_preview()

	def debug_message(self, message):
		""" Write a debug message.
		If debug_ptr was set to a function during init, this will
		write pass the message to that function, else it will just print it.
		This is used mainly to get updates on image capture into the Wenet downlink.

		"""
		message = "PiCam Debug: " + message
		if self.debug_ptr != None:
			self.debug_ptr(message)
		else:
			print(message)

	def close(self):
		self.cam.close()

	def capture(self, filename='output.jpg'):
		# Attempt to capture a set of images.
		for i in range(self.num_images):
			self.debug_message("Capturing Image %d of %d" % (i+1,self.num_images))
			# Wrap this in error handling in case we lose the camera for some reason.
			try:
				self.cam.capture("%s_%d.jpg" % (self.temp_filename_prefix,i))
			except Exception as e: # TODO: Narrow this down...
				self.debug_message("ERROR: %s" % str(e))
				# Immediately return false. Not much point continuing to try and capture images.
				return False

		
		# Otherwise, continue to pick the 'best' image based on filesize.
		self.debug_message("Choosing Best Image.")
		pic_list = glob.glob("%s_*.jpg" % self.temp_filename_prefix)
		pic_sizes = []
		# Iterate through list of images and get the file sizes.
		for pic in pic_list:
			pic_sizes.append(os.path.getsize(pic))
		largest_pic = pic_list[pic_sizes.index(max(pic_sizes))]

		# Copy best image to target filename.
		self.debug_message("Copying image to storage.")
		os.system("cp %s %s" % (largest_pic, filename))
		# Clean up temporary images.
		os.system("rm %s_*.jpg" % self.temp_filename_prefix)

		return True 



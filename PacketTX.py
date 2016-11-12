#!/usr/bin/env python
#
# Serial Packet Transmitter Class
#
# Frames packets (preamble, unique word, checksum)
# and transmits them out of a serial port.
#
#	RPI UART Calibration
#	9600  -> 9600.1536
#	19200 -> 19200.307
#	38400 -> 38339.148
#	57600 -> 57693.417
#  115200 -> 115386.834
#
# Mark Jessop <vk5qi@rfhead.net>
#


import serial,Queue,sys,crcmod,struct
from time import sleep
from threading import Thread
import numpy as np
from ldpc_encoder import *

# Alternate output module, which writes transmitted data as one-bit-per-char (i.e. 0 = 0x00, 1 = 0x01)
# to a file. Very useful for debugging.
class BinaryDebug(object):
	def __init__(self):
		self.f = open("debug.bin",'wb')

	def write(self,data):
		# TODO: Add in RS232 framing
		raw_data = np.array([],dtype=np.uint8)
		for d in data:
			d_array = np.unpackbits(np.fromstring(d,dtype=np.uint8))
			raw_data = np.concatenate((raw_data,[0],d_array[::-1],[1]))

		self.f.write(raw_data.astype(np.uint8).tostring())

	def close(self):
		self.f.close()

def write_debug_message(message, debug_file = "tx_idle_message.txt"):
	#f = open(debug_file,'w')
	#f.write(message)
	#f.close()
	print("DEBUG MSG: %s" % message)

class PacketTX(object):
	txqueue = Queue.Queue(4096) # Up to 1MB of 256 byte packets
	transmit_active = False
	debug = False

	unique_word = "\xab\xcd\xef\x01"
	preamble = "\x55"*16
	idle_sequence = "\x55"*256


	def __init__(self,serial_port="/dev/ttyAMA0", serial_baud=115200, payload_length=256, fec=False, debug = False, callsign="N0CALL"):
		# WARNING: 115200 baud is ACTUALLY 115386.834 baud, as measured using a freq counter.
		if debug == True:
			self.s = BinaryDebug()
			self.debug = True
		else:
			self.s = serial.Serial(serial_port,serial_baud)
		self.payload_length = payload_length

		self.crc16 = crcmod.predefined.mkCrcFun('crc-ccitt-false')
		self.callsign = callsign
		self.idle_message = "DE %s" % callsign
		self.fec = fec

	def start_tx(self):
		self.transmit_active = True
		txthread = Thread(target=self.tx_thread)
		txthread.start()

	def frame_packet(self,packet, fec=False):
		# Ensure payload size is equal to the desired payload length
		if len(packet) > self.payload_length:
			packet = packet[:self.payload_length]

		if len(packet) < self.payload_length:
			packet = packet + "\x00"*(self.payload_length - len(packet))

		crc = struct.pack("<H",self.crc16(packet))

		if fec:
			return self.preamble + self.unique_word + packet + crc + ldpc_encode_string(packet+crc)
		else:
			return self.preamble + self.unique_word + packet + crc 


	def set_idle_message(self, message):
		temp_msg = "\x00" + "DE %s: \t%s" % (self.callsign, message)
		self.idle_message = self.frame_packet(temp_msg)


	# Either generate an idle message, or read one in from a file (tx_idle_message.txt) if it exists.
	# This might be a useful way of getting error messages down from the payload.
	def generate_idle_message(self):
		# Append a \x00 control code before the data
		return "\x00" + "DE %s: \t%s" % (self.callsign,self.idle_message)


	def tx_thread(self):
		while self.transmit_active:
			if self.txqueue.qsize()>0:
				packet = self.txqueue.get_nowait()
				self.s.write(packet)
			else:
				if not self.debug:
					#self.s.write(self.idle_sequence)
					self.s.write(self.idle_message)
				else:
					sleep(0.05)
		
		print("Closing Thread")
		self.s.close()

	def close(self):
		self.transmit_active = False

	def wait(self):
		while not self.txqueue.empty():
			sleep(0.01)

	def tx_packet(self,packet,blocking = False):
		self.txqueue.put(self.frame_packet(packet, self.fec))

		if blocking:
			while not self.txqueue.empty():
				sleep(0.01)




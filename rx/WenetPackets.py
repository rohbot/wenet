#!/usr/bin/env python2.7
#
# Wenet Packet Generators / Decoders
#
import struct

WENET_IMAGE_UDP_PORT 		= 7890
WENET_TELEMETRY_UDP_PORT 	= 7891



class WENET_PACKET_TYPES:
	TEXT_MESSAGE			= 0x00
	TELEMETRY 				= 0x01
	# Your packet types here!
	SSDV 					= 0x55



def decode_packet_type(packet):
	# Convert packet to a list of integers before parsing.
	packet = list(bytearray(packet))
	return packet[0]


def packet_to_string(packet):
	packet_type = decode_packet_type(packet)

	if packet_type == WENET_PACKET_TYPES.TEXT_MESSAGE:
		return text_message_string(packet)
	elif packet_type == WENET_PACKET_TYPES.TELEMETRY:
		return telemetry_string(packet)
	elif packet_type == WENET_PACKET_TYPES.SSDV:
		return ssdv_packet_string(packet)
	else:
		return "Unknown Packet Type: %d" % packet_type



#
# SSDV - Packets as per https://ukhas.org.uk/guides:ssdv
#
def ssdv_packet_info(packet):
	""" Extract various information out of a SSDV packet, and present as a dict. """
	packet = list(bytearray(packet))
	# Check packet is actually a SSDV packet.
	if len(packet) != 256:
		return {'error': "ERROR: Invalid Packet Length"}

	if packet[0] != 0x55: # A first byte of 0x55 indicates a SSDV packet.
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

def ssdv_packet_string(packet):
	""" Produce a textual representation of a SSDV packet. """
	packet_info = ssdv_packet_info(packet)
	if packet_info['error'] != 'None':
		return "SSDV: Unable to decode."
	else:
		return "SSDV: %s, Img:%d, Pkt:%d, %dx%d" % (packet_info['packet_type'],packet_info['image_id'],packet_info['packet_id'],packet_info['width'],packet_info['height'])

#
# Text Messages
#
def decode_text_message(packet):
	""" Extract information from a text message packet """
	# We need the packet as a string, convert to a string in case we were passed a list of bytes.
	packet = str(bytearray(packet))
	message = {}
	try:
		message['len'] = struct.unpack("B",packet[1])[0]
		message['id'] = struct.unpack(">H",packet[2:4])[0]
		message['text'] = packet[4:4+message['len']]
		message['error'] = 'None'
	except:
		return {'error': 'Could not decode message packet.'}

	return message

def text_message_string(packet):
	message = decode_text_message(packet)

	if message['error'] != 'None':
		return "Text: ERROR Could not decode."
	else:
		return "Text Message #%d: \t%s" % (message['id'],message['text'])

#
# GPS/IMU Telemetry
#
def telemetry_string(packet):
	return "Not Implemented."
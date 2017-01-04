#!/usr/bin/env python2.7
#
# Wenet Packet Generators / Decoders
#
import struct
import traceback
import datetime

WENET_IMAGE_UDP_PORT 		= 7890
WENET_TELEMETRY_UDP_PORT 	= 7891



class WENET_PACKET_TYPES:
	TEXT_MESSAGE			= 0x00
	GPS_TELEMETRY 			= 0x01
	ORIENTATION_TELEMETRY	= 0x02
	IMAGE_TELEMETRY			= 0x54
	SSDV 					= 0x55
	IDLE					= 0x56

class WENET_PACKET_LENGTHS:
	GPS_TELEMETRY 		= 35

def decode_packet_type(packet):
	# Convert packet to a list of integers before parsing.
	packet = list(bytearray(packet))
	return packet[0]


def packet_to_string(packet):
	packet_type = decode_packet_type(packet)

	if packet_type == WENET_PACKET_TYPES.TEXT_MESSAGE:
		return text_message_string(packet)
	elif packet_type == WENET_PACKET_TYPES.GPS_TELEMETRY:
		return gps_telemetry_string(packet)
	elif packet_type == WENET_PACKET_TYPES.ORIENTATION_TELEMETRY:
		return orientation_telemetry_string(packet)
	elif packet_type == WENET_PACKET_TYPES.IMAGE_TELEMETRY:
		return image_telemetry_string(packet)
	elif packet_type == WENET_PACKET_TYPES.SSDV:
		return ssdv_packet_string(packet)
	else:
		return "Unknown Packet Type: %d" % packet_type



#
# SSDV - Packets as per https://ukhas.org.uk/guides:ssdv
#

_ssdv_callsign_alphabet = '-0123456789---ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def ssdv_decode_callsign(code):
	code = str(bytearray(code))
	code = struct.unpack('>I',code)[0]
	callsign = ''
	while code:
		callsign += _ssdv_callsign_alphabet[code % 40]
		code /= 40
    
	return callsign

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
			'callsign' : ssdv_decode_callsign(packet[2:6]), # TODO: Callsign decoding.
			'packet_type' : "FEC" if (packet[1]==0x66) else "No-FEC",
			'image_id' : packet[6],
			'packet_id' : (packet[7]<<8) + packet[8],
			'width' : packet[9]*16,
			'height' : packet[10]*16,
			'error' : "None"
		}

		return packet_info
	except Exception as e:
		traceback.print_exc()
		return {'error': "ERROR: %s" % str(e)}

def ssdv_packet_string(packet):
	""" Produce a textual representation of a SSDV packet. """
	packet_info = ssdv_packet_info(packet)
	if packet_info['error'] != 'None':
		return "SSDV: Unable to decode."
	else:
		return "SSDV: %s, Callsign: %s, Img:%d, Pkt:%d, %dx%d" % (packet_info['packet_type'],packet_info['callsign'],packet_info['image_id'],packet_info['packet_id'],packet_info['width'],packet_info['height'])

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
# GPS Telemetry Decoder
#
# Refer Telemetry format documented in:
# https://docs.google.com/document/d/12230J1X3r2-IcLVLkeaVmIXqFeo3uheurFakElIaPVo/edit?usp=sharing
#
# The above 

def gps_weeksecondstoutc(gpsweek, gpsseconds, leapseconds):
    """ Convert time in GPS time (GPS Week, seconds-of-week) to a UTC timestamp """
    epoch = datetime.datetime.strptime("1980-01-06 00:00:00","%Y-%m-%d %H:%M:%S")
    elapsed = datetime.timedelta(days=(gpsweek*7),seconds=(gpsseconds+leapseconds))
    timestamp = epoch + elapsed
    return timestamp.isoformat()

def gps_telemetry_decoder(packet):
	""" Extract GPS telemetry data from a packet, and return it as a dictionary. 

	Keyword Arguments:
	packet:	A GPS telemetry packet, as per https://docs.google.com/document/d/12230J1X3r2-IcLVLkeaVmIXqFeo3uheurFakElIaPVo/edit?usp=sharing
			This can be provided as either a string, or a list of integers, which will be converted
			to a string prior to decoding.

	Return value:
			A dictionary containing the decoded packet data. 
			If the decode failed for whatever reason, a dictionary will still be returned, but will 
			contain the field 'error' with the decode fault description.
			This field (error) will be set to 'None' if decoding was successful.

	"""

	# We need the packet as a string - convert to a string in case we were passed a list of bytes,
	# which occurs when we are decoding a packet that has arrived via a UDP-broadcast JSON blob.
	packet = str(bytearray(packet))
	gps_data = {}

	# Some basic sanity checking of the packet before we attempt to decode.
	if len(packet) < WENET_PACKET_LENGTHS.GPS_TELEMETRY:
		return {'error': 'GPS Telemetry Packet has invalid length.'}
	elif len(packet) > WENET_PACKET_LENGTHS.GPS_TELEMETRY:
		# If the packet is too big (which it will be, as it's padded with 0x55's), clip it. 
		packet = packet[:WENET_PACKET_LENGTHS.GPS_TELEMETRY]
	else:
		pass

	# Wrap the next bit in exception handling.
	try:
		# Unpack the packet into a list.
		data = struct.unpack('>BHIBffffffBBB', packet)

		gps_data['week'] 	= data[1]
		gps_data['iTOW'] 	= data[2]/1000.0 # iTOW provided as milliseconds, convert to seconds.
		gps_data['leapS'] 	= data[3]
		gps_data['latitude'] = data[4]
		gps_data['longitude'] = data[5]
		gps_data['altitude'] = data[6]
		gps_data['ground_speed'] = data[7]
		gps_data['heading'] = data[8]
		gps_data['ascent_rate'] = data[9]
		gps_data['numSV'] 	= data[10]
		gps_data['gpsFix']	= data[11]
		gps_data['dynamic_model'] = data[12]

		# Perform some post-processing on the data, to make some of the fields easier to read.

		# Produce a human-readable timestamp, in UTC time.
		gps_data['timestamp'] = gps_weeksecondstoutc(gps_data['week'], gps_data['iTOW'], gps_data['leapS'])

		# Produce a human-readable indication of GPS Fix state.
		if gps_data['gpsFix'] == 0:
			gps_data['gpsFix_str'] = 'No Fix'
		elif gps_data['gpsFix'] == 2:
			gps_data['gpsFix_str'] = '2D Fix'
		elif gps_data['gpsFix'] == 3:
			gps_data['gpsFix_str'] = '3D Fix'
		elif gps_data['gpsFix'] == 5:
			gps_data['gpsFix_str'] = 'Time Only'
		else:
			gps_data['gpsFix_str'] = 'Unknown (%d)' % gps_data['gpsFix']

		# Produce a human-readable indication of the current dynamic model.
		if gps_data['dynamic_model'] == 0:
			gps_data['dynamic_model_str'] = 'Portable'
		elif gps_data['dynamic_model'] == 1:
			gps_data['dynamic_model_str'] = 'Not Used'
		elif gps_data['dynamic_model'] == 2:
			gps_data['dynamic_model_str'] = 'Stationary'
		elif gps_data['dynamic_model'] == 3:
			gps_data['dynamic_model_str'] = 'Pedestrian'
		elif gps_data['dynamic_model'] == 4:
			gps_data['dynamic_model_str'] = 'Automotive'
		elif gps_data['dynamic_model'] == 5:
			gps_data['dynamic_model_str'] = 'Sea'
		elif gps_data['dynamic_model'] == 6:
			gps_data['dynamic_model_str'] = 'Airborne 1G'
		elif gps_data['dynamic_model'] == 7:
			gps_data['dynamic_model_str'] = 'Airborne 2G'
		elif gps_data['dynamic_model'] == 8:
			gps_data['dynamic_model_str'] = 'Airborne 4G'
		else:
			gps_data['dynamic_model_str'] = 'Unknown'

		gps_data['error'] = 'None'

		return gps_data

	except:
		traceback.print_exc()
		print(packet)
		return {'error': 'Could not decode GPS telemetry packet.'}


def gps_telemetry_string(packet):
	""" Produce a String representation of a GPS Telemetry packet"""

	# Decode packet to a dictionary 
	gps_data = gps_telemetry_decoder(packet)

	# Check if there was a decode error. If not, produce a string.
	if gps_data['error'] != 'None':
		return "GPS: ERROR Could not decode."
	else:
		gps_data_string = "GPS: %s Lat/Lon: %.5f,%.5f Alt: %dm, Speed: H %dkph V %.1fm/s, Heading: %d deg, Fix: %s, SVs: %d, Model: %s " % (
			gps_data['timestamp'],
			gps_data['latitude'],
			gps_data['longitude'],
			int(gps_data['altitude']),
			int(gps_data['ground_speed']),
			gps_data['ascent_rate'],
			int(gps_data['heading']),
			gps_data['gpsFix_str'],
			gps_data['numSV'],
			gps_data['dynamic_model_str']
			)

		return gps_data_string

#
# Orientation Telemetry Decoder
#
def orientation_telemetry_decoder(packet):
	""" Extract Orientation Telemetry data from a supplied packet, and return it as a dictionary.

	Keyword Arguments:
	packet:	An Orientation telemetry packet, as per https://docs.google.com/document/d/12230J1X3r2-IcLVLkeaVmIXqFeo3uheurFakElIaPVo/edit?usp=sharing
			This can be provided as either a string, or a list of integers, which will be converted
			to a string prior to decoding.

	Return value:
			A dictionary containing the decoded packet data. 
			If the decode failed for whatever reason, a dictionary will still be returned, but will 
			contain the field 'error' with the decode fault description.
			This field (error) will be set to 'None' if decoding was successful.

	"""

	# We need the packet as a string - convert to a string in case we were passed a list of bytes,
	# which occurs when we are decoding a packet that has arrived via a UDP-broadcast JSON blob.
	packet = str(bytearray(packet))

	# SHSSP Code goes here.

	return {'error': "Orientation: Not Implemented."}

def orientation_telemetry_string(packet):
	""" Produce a String representation of an Orientation Telemetry packet"""

	return "Orientation: Not Implemented Yet."


#
# Image (Combined GPS/Orientation + Image ID) Telemetry Decoder
#
def image_telemetry_decoder(packet):
	""" Extract Image Telemetry data from a supplied packet, and return it as a dictionary.

	Keyword Arguments:
	packet:	An Image telemetry packet, as per https://docs.google.com/document/d/12230J1X3r2-IcLVLkeaVmIXqFeo3uheurFakElIaPVo/edit?usp=sharing
			This can be provided as either a string, or a list of integers, which will be converted
			to a string prior to decoding.

	Return value:
			A dictionary containing the decoded packet data. 
			If the decode failed for whatever reason, a dictionary will still be returned, but will 
			contain the field 'error' with the decode fault description.
			This field (error) will be set to 'None' if decoding was successful.

	"""

	# We need the packet as a string - convert to a string in case we were passed a list of bytes,
	# which occurs when we are decoding a packet that has arrived via a UDP-broadcast JSON blob.
	packet = str(bytearray(packet))

	# SHSSP Code goes here.

	return {'error': "Image Telemetry: Not Implemented."}

def image_telemetry_string(packet):
	""" Produce a String representation of an Image Telemetry packet"""
	
	return "Image Telemetry: Not Implemented Yet."
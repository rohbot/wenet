#%%
import codecs
import struct
import datetime
import logging
import os
import socket
log_level = logging.DEBUG

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=log_level)
logging.getLogger("requests").setLevel(logging.DEBUG)

from horusdemodlib.habitat import HabitatUploader
from horusdemodlib.decoder import parse_ukhas_string
import serial
import json
import sys
ser = serial.Serial('/dev/ttyACM0', 57600, timeout=0)
ser.write(b"~F915.335\r") # Set frequency
ser.write(b"~M2\r") # Set Mode, this seems to work

lat = '-37.775249'
lng = '145.111160'

# uploader = HabitatUploader(user_callsign="RPHMELB-LORA",listener_lat=lat, listener_lon=lng)

WENET_IMAGE_UDP_PORT        = 7890
WENET_TELEMETRY_UDP_PORT    = 55672

SSDV_PAYLOAD = []
reading_ssdv = False

def decode_packet_type(packet):
    # Convert packet to a list of integers before parsing.
    packet = list(bytearray(packet))
    return packet[0]
# %%
_ssdv_callsign_alphabet = '-0123456789---ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def ssdv_decode_callsign(code):
    """ Decode a SSDV callsign from a supplied array of ints,
        extract from a SSDV packet.
        Args:
            list: List of integers, corresponding to bytes 2-6 of a SSDV packet.
        Returns:
            str: Decoded callsign.
    """

    code = bytes(bytearray(code))
    code = struct.unpack('>I',code)[0]
    callsign = ''

    while code:
        callsign += _ssdv_callsign_alphabet[code % 40]
        code = code // 40
    
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
        print(e)
        return {'error': "ERROR: %s" % str(e)}

def ssdv_packet_string(packet):
    """ Produce a textual representation of a SSDV packet. """
    packet_info = ssdv_packet_info(packet)
    if packet_info['error'] != 'None':
        return "SSDV: Unable to decode."
    else:
        return "SSDV: %s, Callsign: %s, Img:%d, Pkt:%d, %dx%d" % (packet_info['packet_type'],packet_info['callsign'],packet_info['image_id'],packet_info['packet_id'],packet_info['width'],packet_info['height'])

# GUI updates are only sent locally.
def trigger_gui_update(filename, text = "None"):
	message = 	{'filename': filename,
				'text': text}

	gui_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	gui_socket.sendto(json.dumps(message).encode('ascii'),("127.0.0.1",WENET_IMAGE_UDP_PORT))
	gui_socket.close()

current_image = -1
current_callsign = ""
current_text_message = -1
current_packet_count = 0
current_packet_time = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")
partialupdate = 0
# Open temporary file for storing data.
temp_f = open("rxtemp.bin",'wb')

#Read serial
while 1:
  line = ser.readline().decode().strip()
  if len(line) < 1:
    continue
    
  if 'Message' in line:
    msg = line.replace("Message=", "")
    try:
        payload = parse_ukhas_string(msg)
        print(payload)
        #uploader.habitat_upload(msg)
    except:
        print("bad payload", msg)
    
    #uploader.habitat_upload(msg)
    #payload = json.dumps({"timestamp": time.time(), "telemetry" : msg})
    
  elif 'Hex=' in line:
    reading_ssdv = True
    print("Incoming SSDV", line)
    SSDV_PAYLOAD.append(line)
  elif '=' in line:
    if reading_ssdv:
        reading_ssdv = False
        p = ''.join(SSDV_PAYLOAD).replace('Hex=','')
        print(p)

        data = codecs.decode(p, 'hex')
        packet = list(bytearray(data))
        packet.insert(0, 85)
        data = bytearray(packet)

        packet_info = ssdv_packet_info(data)
        packet_as_string = ssdv_packet_string(data)
        print(packet_info)
        # Only proceed if there are no decode errors.
        if packet_info['error'] != 'None':
          logging.error(packet_info['error'])
          continue

        if (packet_info['image_id'] != current_image) or (packet_info['callsign'] != current_callsign) :
          # Attempt to decode current image if we have enough packets.
          logging.info("New image - ID #%d" % packet_info['image_id'])
          if current_packet_count > 0:
            # Attempt to decode current image, and write out to a file.
            temp_f.close()
            # Run SSDV
            returncode = os.system("ssdv -d rxtemp.bin ./rx_images/%s_%s_%d.jpg 2>/dev/null > /dev/null" % (current_packet_time,current_callsign,current_image))
            if returncode == 1:
              logging.error("ERROR: SSDV Decode failed!")
            else:
              logging.debug("SSDV Decoded OK!")
              # Make a copy of the raw binary data.
              os.system("mv rxtemp.bin ./rx_images/%s_%s_%d.bin" % (current_packet_time,current_callsign,current_image))

              # # Update live displays here.
              trigger_gui_update(os.path.abspath("./rx_images/%s_%s_%d.jpg" % (current_packet_time,current_callsign,current_image)), packet_as_string)

              # Trigger upload to habhub here.
          else:
            logging.debug("Not enough packets to decode previous image.")

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
        SSDV_PAYLOAD = []
  else:
    if reading_ssdv:
        SSDV_PAYLOAD.append(line)
    else:
        print(line)
    
#!/usr/bin/env python
#
#   Emulate the function of a wenet downlink system, to enable testing of the secondary
#   packet functionality.
#   
#   Note that these scripts ONLY work in Python 2 at the moment (sorry...)
#
#   To use this, start this script in a terminal window with:
#   $ python wenet_link_emulation.py
#
#   You may then start up the secondary payload tx example script in another terminal with:
#   $ python sec_payload_tx_example.py
#   which will start emitting example text and floating point packets.
#
#   In yet another terminal, navigate to the wenet/rx/ directory and run:
#   $ python sec_payload_rx_example.py
#
#   The 'received' secondary payload packets will be displayed as if they were received via a wenet link.
#
#   Copyright (C) 2019  Mark Jessop <vk5qi@rfhead.net>
#   Released under GNU GPL v3 or later
#

import json
import socket
import struct
import datetime
import traceback

WENET_SECONDARY_UDP_PORT = 55674
WENET_TELEMETRY_UDP_PORT = 55672


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

    # Place data into dictionary.
    data = {'type': 'WENET', 'packet': list(bytearray(data))}

    # Send to broadcast if we can.
    try:
        telemetry_socket.sendto(json.dumps(data), ('<broadcast>', WENET_TELEMETRY_UDP_PORT))
    except socket.error:
        telemetry_socket.sendto(json.dumps(data), ('127.0.0.1', WENET_TELEMETRY_UDP_PORT))

    telemetry_socket.close()


def generate_secondary_payload_packet(id=1, data=[], repeats=1):
    """ Generate  packet supplied by a 'secondary' payload.
    These will usually be provided via a UDP messaging system, described in the functions
    further below.

    Keyword Arguments:
    id (int): A payload ID number, 0-255.
    data (list): The payload contents, as a list of integers. Maximum of 254 bytes.
    repeats (int): (Optional) The number of times to transmit this packet.
    """

    # Clip the id to 0-255.
    _id = int(id) % 256

    # Convert the provided data to a string
    _data = str(bytearray(data))
    # Clip to 254 bytes.
    if len(_data) > 254:
        _data = _data[:254]

    
    _packet = "\x03" + struct.pack(">B",_id) + _data

    return _packet


def process_udp(udp_packet):
    """ Process received UDP packets. """

    # Parse JSON
    packet_dict = json.loads(udp_packet)

    # There may be other UDP traffic on this port, so we filter for just 'WENET'
    # telemetry packets.
    if packet_dict['type'] == 'WENET_TX_SEC_PAYLOAD':
        # Extract packet and secondary payload ID number.
        packet = packet_dict['packet']
        _id = packet_dict['id']

        # Generate a 'secondary payload' packet, as would be transmitted.
        _packet_blob = generate_secondary_payload_packet(id=_id, data=packet)

        # Broadcast it via UDP.
        broadcast_telemetry_packet(_packet_blob)

        print("Repeated packet from ID: %d" % (_id))


def udp_rx_thread():
    """ Listen on a port for UDP broadcast packets, and pass them onto process_udp()"""
    global udp_listener_running
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.settimeout(1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except:
        pass

    s.bind(('',WENET_SECONDARY_UDP_PORT))
    print("Started UDP Listener")
    while True:
        try:
            m = s.recvfrom(2048)
        except socket.timeout:
            m = None
        
        if m != None:
            try:
                process_udp(m[0])
            except:
                traceback.print_exc()
                pass
    
    print("Closing UDP Listener")
    s.close()


if __name__ == "__main__":
    try:
        # Start listening for UDP packets
        udp_rx_thread()

    # Keep on going until we get Ctrl-C'd
    except KeyboardInterrupt:
        # Stop the UDP listener.
        udp_listener_running = False
#!/usr/bin/env python2.7
#
# Basic Wenet Text Message / Telemetry Viewer.
#
#   Copyright (C) 2018  Mark Jessop <vk5qi@rfhead.net>
#   Released under GNU GPL v3 or later
#
# Will eventually form the basis of a GUI.


import json
import socket
import datetime
import traceback
from WenetPackets import *

log_file = open('telemetry.log', 'a')

def process_udp(udp_packet):
    """ Process received UDP packets. """
    # Grab timestamp.
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")

    # Parse JSON, and extract packet.
    packet_dict = json.loads(udp_packet)
    packet = packet_dict['packet']

    # Convert to string, and print to terminal with timestamp.
    telem_string = "%s \t%s" % (timestamp,packet_to_string(packet))

    print(telem_string)
    log_file.write(telem_string + "\n")
    log_file.flush()



udp_listener_running = False
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
    s.bind(('',WENET_TELEMETRY_UDP_PORT))
    print("Started UDP Listener Thread.")
    udp_listener_running = True
    while udp_listener_running:
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
        udp_rx_thread()
    except KeyboardInterrupt:
        udp_listener_running = False
#!/usr/bin/env python
#
#   Wenet Web GUI
#
#   Copyright (C) 2019  Mark Jessop <vk5qi@rfhead.net>
#   Released under GNU GPL v3 or later
#
#   A really hacky first attempt at a live-updating web interface that displays wenet imagery.
#
#   Run this instead of rx_gui in the startup scripts, and then access at http://localhost:5003/
#
#   TODO:
#       [ ] Automatic re-scaling of images in web browser.
#       [ ] Add Display of GPS telemetry and text messages.
#
import json
import logging
import flask
from flask_socketio import SocketIO
import time
import traceback
import socket
import sys
import datetime
from threading import Thread, Lock
from io import BytesIO

WENET_IMAGE_UDP_PORT = 7890

# Define Flask Application, and allow automatic reloading of templates for dev
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# SocketIO instance
socketio = SocketIO(app)


# Latest Image
latest_image = None
latest_image_lock = Lock()


#
#   Flask Routes
#

@app.route("/")
def flask_index():
    """ Render main index page """
    return flask.render_template('index.html')


@app.route("/latest.jpg")
def serve_latest_image():
    global latest_image, latest_image_lock
    if latest_image == None:
        flask.abort(404)
    else:
        # Grab image bytes.
        latest_image_lock.acquire()
        _temp_image = bytes(latest_image)
        latest_image_lock.release()

        return flask.send_file(
            BytesIO(_temp_image),
            mimetype='image/jpeg',
            as_attachment=False)



def flask_emit_event(event_name="none", data={}):
    """ Emit a socketio event to any clients. """
    socketio.emit(event_name, data, namespace='/update_status') 


# SocketIO Handlers

@socketio.on('client_connected', namespace='/update_status')
def update_client_display(data):
    pass



def update_image(filename, description):
    global latest_image, latest_image_lock
    try:
        with open(filename, 'rb') as _new_image:
            _data = _new_image.read()

        latest_image_lock.acquire()
        latest_image = bytes(_data)
        latest_image_lock.release()

        # Trigger the clients to update.
        flask_emit_event('image_update', data={'text':description})

        logging.debug("Loaded new image: %s" % filename)

    except Exception as e:
        logging.error("Error loading new image %s - %s" % (filename, str(e)))



def process_udp(packet):

    packet_dict = json.loads(packet.decode('ascii'))

    if 'filename' in packet_dict:
        # New image to load
        update_image(packet_dict['filename'], packet_dict['text'])

    elif 'uploader_status' in packet_dict:
        # Information from the uploader process.
        flask_emit_event('uploader_update', data=packet_dict)



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
    s.bind(('',WENET_IMAGE_UDP_PORT))
    logging.info("Started UDP Listener Thread.")
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
    
    logging.info("Closing UDP Listener")
    s.close()



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--listen_port",default=5003,help="Port to run Web Server on. (Default: 5003)")
    args = parser.parse_args()


    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)


    t = Thread(target=udp_rx_thread)
    t.start()

    # Run the Flask app, which will block until CTRL-C'd.
    socketio.run(app, host='0.0.0.0', port=args.listen_port)

    udp_listener_running = False




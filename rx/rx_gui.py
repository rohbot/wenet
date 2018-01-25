#!/usr/bin/env python
#
#   SSDV RX GUI
#
#   Copyright (C) 2018  Mark Jessop <vk5qi@rfhead.net>
#   Released under GNU GPL v3 or later
#

from WenetPackets import *
import sip, socket, Queue, json
from threading import Thread
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

# Auto-resizing Widget, to contain displayed image.
class Label(QtGui.QLabel):
    def __init__(self, img):
        super(Label, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.pixmap = QtGui.QPixmap()

    def paintEvent(self, event):
        size = self.size()
        painter = QtGui.QPainter(self)
        point = QtCore.QPoint(0,0)
        scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, transformMode = Qt.SmoothTransformation)
        # start painting the label from left upper corner
        point.setX((size.width() - scaledPix.width())/2)
        point.setY((size.height() - scaledPix.height())/2)
        #print point.x(), ' ', point.y()
        painter.drawPixmap(point, scaledPix)

class MyWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.label = Label(self)
        self.statusLabel = QtGui.QLabel("No Updates Yet...")
        self.statusLabel.setFixedHeight(30)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.statusLabel)

        self.rxqueue = Queue.Queue(16)

    @QtCore.pyqtSlot(str)
    def changeImage(self, pathToImage, text_message):
        print(pathToImage)
        pixmap = QtGui.QPixmap(pathToImage)
        self.label.pixmap = pixmap
        self.label.repaint()
        self.statusLabel.setText(text_message)
        print("Repainted")

    def read_queue(self):
        try:
            new_packet = self.rxqueue.get_nowait()
            packet_data = json.loads(new_packet)
            self.changeImage(packet_data['filename'],packet_data['text'])
        except:
            pass

# UDP Listener
udp_listener_running = False
udp_callback = None
def udp_rx():
    global udp_listener_running, udp_callback
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.settimeout(1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('',WENET_IMAGE_UDP_PORT))
    print("Started UDP Listener Thread.")
    udp_listener_running = True
    while udp_listener_running:
        try:
            m = s.recvfrom(512)
        except socket.timeout:
            m = None
        
        if m != None:
            udp_callback(m[0])

    print("Closing UDP Listener")
    s.close()

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('SSDV Viewer')

    main = MyWindow()
    main.resize(800,600)
    main.setWindowTitle("SSDV Viewer")

    udp_callback = main.rxqueue.put_nowait
    t = Thread(target=udp_rx)
    t.start()

    timer = QtCore.QTimer()
    timer.timeout.connect(main.read_queue)
    timer.start(100)

    main.show()

    app.exec_()

    udp_listener_running = False

    sys.exit()

#!/usr/bin/env python
#
# 	RFM98W Initialisation for Wenet Telemetry
#
#	2016-11-18 Mark Jessop <vk5qi@rfhead.net>
#
#	Requires pySX127x:
#	https://github.com/darksidelemm/pySX127x
#   Copy the SX127x directory into this directory... 
#
#	Uses spidev for comms with a RFM98W module.
#
#	Note: As with the RFM22B version, all this script does
#	is get the RFM98W onto the right frequency, and into the right mode.
#
#	SPI: Connected to CE0 (like most of my LoRa shields)
#	RPi TXD: Connected to RFM98W's DIO2 pin.
#
from SX127x.LoRa import *
from SX127x.hardware_piloragateway import HardwareInterface

import sys


if __name__ == '__main__':

    # Attempt to extract a frequency from the first argument:
    if len(sys.argv)<2:
        print("Usage: \tpython init_rfm98w.py <TX Frequency in MHz>")
        print("Example: \tpython init_rfm98w.py 441.200")
        print("Alternate usage: python init_rfm98w.py shutdown")
        sys.exit(1)

    shutdown = False
    tx_freq = 441.200

    try:
        tx_freq = float(sys.argv[1])
    except:
        if sys.argv[1] == "shutdown":
            shutdown = True
        else:
            print("Unable to parse input.")

    if tx_freq>450.0 or tx_freq<430.00:
        print("Frequency out of 70cm band, using default.")
        tx_freq = 441.200

    # Set this to 1 if your RFM98W is on CE1
    hw = HardwareInterface(0)

    # Start talking to the module...
    lora = LoRa(hw)
    
    # Set us into FSK mode, and set continuous mode on
    lora.set_register(0x01,0x00) # Standby Mode
    # If we have been asked to shutdown the RFM98W, then exit here.
    if shutdown:
        sys.exit(0)

    # Otherwise, proceed.
    lora.set_register(0x31,0x00) # Set Continuous Mode
    
    # Set TX Frequency
    lora.set_freq(tx_freq)

    # Set Deviation (~70 kHz). Signals ends up looking a bit wider than the RFM22B version.
    lora.set_register(0x04,0x04)
    lora.set_register(0x05,0x99)
  
    # Set Transmit power to 50mW
    lora.set_register(0x09,0x8F)

    # Go into TX mode.
    lora.set_register(0x01,0x02) # .. via FSTX mode (where the transmit frequency actually gets set)
    lora.set_register(0x01,0x03) # Now we're in TX mode...

#!/usr/bin/env python
#
# 	RFM98W Initialisation for Wenet Telemetry
#
#   Copyright (C) 2018  Mark Jessop <vk5qi@rfhead.net>
#   Released under GNU GPL v3 or later
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
import sys
import argparse
from SX127x.LoRa import *
from SX127x.hardware_piloragateway import HardwareInterface

def setup_rfm98w(frequency=441.200, spi_device=0, shutdown=False):
    # Set this to 1 if your RFM98W is on CE1
    hw = HardwareInterface(spi_device)

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
    lora.set_freq(frequency)

    # Set Deviation (~70 kHz). Signals ends up looking a bit wider than the RFM22B version.
    lora.set_register(0x04,0x04)
    lora.set_register(0x05,0x99)
  
    # Set Transmit power to 50mW.
    # NOTE: If you're in another country you'll probably want to modify this value to something legal...
    lora.set_register(0x09,0x8F)

    # Go into TX mode.
    lora.set_register(0x01,0x02) # .. via FSTX mode (where the transmit frequency actually gets set)
    lora.set_register(0x01,0x03) # Now we're in TX mode...

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--frequency", default=441.200, type=float, help="Transmit Frequency (MHz). Default = 441.200 MHz.")
    parser.add_argument("--spidevice", default=0, type=int, help="LoRa SPI Device number. Default = 0.")
    parser.add_argument("--shutdown",action="store_true", help="Shutdown Transmitter instead of activating it.")
    args = parser.parse_args()

    tx_freq = args.frequency

    if tx_freq>450.0 or tx_freq<430.00:
        print("Frequency out of 70cm band, using default.")
        tx_freq = 441.200

    setup_rfm98w(frequency=tx_freq, spi_device=args.spidevice, shutdown=args.shutdown)

    sys.exit(0)



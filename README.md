# Wenet - The Swift One
Transmit and Receive code for the Project Horus High-Speed Imagery Payload - 'Wenet'.


The transmit side is designed to run on a Raspberry Pi, and the UART (/dev/ttyAMA0) is used to modulate a RFM98W (yes, a LoRa module) in direct-asynchronous mode. I expect other transmitters could probably be used (i.e. NTX2's or similar) at lower bandwidths.

## Flight History
* v0.1 - First test flight on Horus 37, no FEC. Read more about that here: http://rfhead.net/?p=637
* v0.2 - Second test flight on Horus 39, with LDPC FEC enabled. Read more here: http://www.rowetel.com/?p=5344
* v0.3 - Third test flight on Horus 40 - 2nd Jan 2017. Added GPS overlay support. Read more here: http://www.areg.org.au/archives/206627
* v0.4 - SHSSP 2017 Launches (Horus 41 & 42) - 22nd Jan 2017. Added IMU and simultaneous capture from two cameras (Visible and Near-IR). Two payloads were flown, each with two cameras. A third payload (same as on Horus 40) was also flown, which captured the image below. Read more here: http://www.areg.org.au/archives/206739
* v0.5 - Minor updates. Flown on Horus 43 through Horus 49.
* v0.6 - Updated to the latest fsk_demod version from codec2-dev. This allows reception without requiring CSDR.
* v0.7 - More tweaks to the start_rx script to better support lower-rate modes. Update to the latest fsk_demod in the instructions.

![Image downlinked via Wenet on Horus 42](http://rfhead.net/temp/horus_42_small.jpg)

The above image was captured on Horus 42, and downlinked via Wenet. The original downlinked resolution was 1920x1440, and has since been re-sized. The full resolution version is available here: http://rfhead.net/temp/horus_42_full.jpg

## Usage Instructions

Refer to the [wiki](https://github.com/projecthorus/wenet/wiki) pages for the latest installation/usage instructions.

## WARNING: The below information is partly outdated. Use the above installation guide.

## Main Programs
* `rx/rx_ssdv.py` - Reads in received packets (256 byte SSDV frames) via stdin, and decodes them to JPEGs. Also informs other processes (via UDP broadcast) of new ssdv and telemetry data.
* `rx/rx_gui.py` - Displays last received image, as commanded by rx_ssdv.py via UDP.
* `tx/init_rfm22b.py` - Set RFM22B (attached via SPI to the RPi) into Direct-Asynchronous mode.
* `tx/init_rfm98w.py` - Set RFM98W (attached via SPI to the RPi) into Direct-Asynchronous mode. Note that this requires pySX127x from https://github.com/darksidelemm/pySX127x
* `tx_picam_gps.py` - Captures pictures using the PiCam, overlays GPS data and transmits them.

## Testing Scripts
* Run `python compress_test_images.py` from within ./test_images/ to produce the set of test ssdv-compressed files.

### TX Testing
* `tx_test_images.py` transmits a stream of test images out of the RPi UART. Check the top of the file for settings.
 * This script can also be used to produce a one-char-per-bit output, which is what would be seen by the modulator.

### RX Testing
* `rx_tester.py` produces a stream of packets on stdout, as would be received from the fsk_demod modem. 
 * Run `python rx_tester.py | python rx_ssdv.py` to feed these test packets into the command-line ssdv rx script.
 * add `--partialupdate N` to the above command to have rx_gui.py update every N received packets.

## Sending/Receiving Images
### TX Side
Refer to the instructions here: https://github.com/projecthorus/wenet/wiki/Wenet-TX-Payload-Instructions

### RX Side
Refer to the instructions here: https://github.com/projecthorus/wenet/wiki/Wenet-RX-Instructions-(Ubuntu-Debian)


## RX Tips.
* It is highly recommended to use a preamplifier in front of your RTLSDR to lower the overall noise figure of the system. With a NooElec RTLSDR (R820T2 Tuner) and a [HabAmp](https://store.uputronics.com/index.php?route=product/product&product_id=53), we were able to achieve a Minimum-Detectable-Signal (MDS - which we defined as the point where we get no packet errors) of around -112 dBm.
* If needed, the transmit bitrate can be slowed down by editing the defaults in tx_picam.py. You will then have to determine the appropriate parameters for fsk_demod and the preceding filtering/resampling chain to be able to receive this bitrate.


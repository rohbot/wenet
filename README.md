# HorusHighSpeed
Modulator and glue code for the 100kbps SSDV experiment.

The transmit side is designed to run on a Raspberry Pi, and the UART (/dev/ttyAMA0) is used to modulate a RFM22B in direct-asynchronous mode. I expect other transmitters could probably be used (i.e. NTX2's or similar) at lower bandwidths.

## Dependencies
* Python (2.7, though 3 might work with some small mods)
* SSDV (https://github.com/fsphil/ssdv)
* crcmod (pip install crcmod)
* numpy (for debug output tests)

## Main Programs
* `rx_ssdv.py` - Reads in received packets (256 byte SSDV frames) via stdin, and decodes them to JPEGs. Also informs other processes (via UDP broadcast) of new data.
* `tx_picam.py` - TODO.

## Testing Scripts
* Run `python compress_test_images.py` from within ./test_images/ to produce the set of test ssdv-compressed files.

### TX Testing
* `tx_test_images.py` transmits a stream of test images out of the RPi UART. Check the top of the file for settings.
 * This script can also be used to produce a one-char-per-bit output, which is what would be seen by the modulator.

### RX Testing
* `rx_tester.py` produces a stream of packets on stdout, as would be received from the fsk_demod modem (from codec2 - still under development).
 * Run `python rx_tester.py | python rx_ssdv.py` to feed these test packets into the command-line ssdv rx script.
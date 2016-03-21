# Wenet - The Swift One
Modulator and glue code for the 115kbps SSDV experiment.

The transmit side is designed to run on a Raspberry Pi, and the UART (/dev/ttyAMA0) is used to modulate a RFM22B in direct-asynchronous mode. I expect other transmitters could probably be used (i.e. NTX2's or similar) at lower bandwidths.

## Dependencies
* Python (2.7, though 3 might work with some small mods)
* SSDV (https://github.com/fsphil/ssdv). The `ssdv` binary needs to be available on the PATH.
* crcmod (`pip install crcmod`)
* numpy (for debug output tests)
* PyQtGraph & PyQt4 (for FSK Modem Stats and SSDV GUI: `pip install pyqtgraph`)

## Main Programs
* `rx_ssdv.py` - Reads in received packets (256 byte SSDV frames) via stdin, and decodes them to JPEGs. Also informs other processes (via UDP broadcast) of new data.
* `rx_gui.py` - Displays last received image, as commanded by rx_ssdv.py via UDP.
* `init_rfm22b.py` - Set RFM22B (attached via SPI to the RPi) into Direct-Asynchronous mode. 
* `tx_picam.py` - Captures pictures using the PiCam, and transmits them.

## Testing Scripts
* Run `python compress_test_images.py` from within ./test_images/ to produce the set of test ssdv-compressed files.

### TX Testing
* `tx_test_images.py` transmits a stream of test images out of the RPi UART. Check the top of the file for settings.
 * This script can also be used to produce a one-char-per-bit output, which is what would be seen by the modulator.

### RX Testing
* `rx_tester.py` produces a stream of packets on stdout, as would be received from the fsk_demod modem (from codec2 - still under development).
 * Run `python rx_tester.py | python rx_ssdv.py` to feed these test packets into the command-line ssdv rx script.
 * add `--partialupdate N` to the above command to have rx_gui.py update every N received packets.

## Sending/Receiving Images
### TX Side
* Run either `python tx_picam.py` (might need sudo) or `python tx_test_images.py` on the transmitter Raspberry Pi.

#### IMPORTANT NOTE
While the transit code requests an output baud rate of 115200 baud from the RPi's UART, the acheived baud rate (due to clock divisors) is actually 115386.843 baud (measured using a frequency counter). All of the resampling within the receive chain has been adjusted accordingly.

### RX Side
To be able to run a full receive chain, from SDR through to images, you'll need:
* GnuRadio + libraries for whatever SDR you plan on using.
* `fsk_demod` and `drs232` from codec2-dev. You can get these using
 * `svn checkout http://svn.code.sf.net/p/freetel/code/codec2-dev/`
 * `cd codec2-dev && mkdir build-linux && cd build-linux && cmake ../`
 * Build `drs232` using `gcc src/drs232.c -o src/drs232 -Wall`
 * Then copy `src/fsk_demod`, `src/drs232` and `octace/fskdemodgui.py` to this directory. 

* A few example gnuradio-companion flow-graphs are in the `grc` directory, for different SDRs. These receive samples from the SDR, demodulate a 500KHz section of spectrum as USB, resamples them to fsbaud*8 (which fsk_demod requires), then presents these samples via a TCP sink, which is acting as a TCP server. You will probably need to modify these to set the appropriate receive frequency.

* To receive the FSK data and display the images 'live', run:
 * In another terminal: `python rx_gui.py`, which will listen via UDP for new images to display.
 * Start the appropriate GNURadio Companion Flowgraph. This will block until a client connects to the TCP Sinks TCP socket on port 9898.
 * Start the FSK modem with:
  * `nc localhost 9898 | ./fsk_demod 2X 8 923096 115387 - - S 2> >(python fskdemodgui.py) | ./drs232 - - | python rx_ssdv.py --partialupdate 8`

### RX Without GNURadio
It's possible to use csdr (Get it from https://github.com/simonyiszk/csdr ) to perform the sideband demodulation and resampling functions:

Example (RTLSDR):
`rtl_sdr -s 1000000 -f 441000000 -g 35 - | csdr convert_u8_f | csdr bandpass_fir_fft_cc 0.1 0.4 0.05 | csdr fractional_decimator_ff 1.08331 | csdr realpart_cf | csdr convert_f_s16 | ./fsk_demod 2X 8 923096 115387 - - S 2> >(python fskdemodgui.py) | ./drs232 - - | python rx_ssdv.py --partialupdate 8`

This gets samples from the rtl_sdr at 1MHz, performs bandpass and fractional decimation options (to get the required Rb*8 sample rate for fsk_demod), then throw away the imaginary part and converts to 16-bit shorts before passing the data to fsk_demod.

Example (AirSpy):
`airspy_rx -f441.0 -r /dev/stdout -a 1 -h 21  | csdr convert_s16_f | csdr bandpass_fir_fft_cc 0.025 0.175 0.025 | csdr fractional_decimator_ff 2.708277 | csdr realpart_cf | csdr convert_f_s16 | ./fsk_demod 2X 8 923096 115387 - - S 2> >(python fskdemodgui.py) | ./drs232 - - | python rx_ssdv.py --partialupdate 8`


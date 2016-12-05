# Wenet - The Swift One
Modulator and glue code for the 115kbps SSDV experiment.

The transmit side is designed to run on a Raspberry Pi, and the UART (/dev/ttyAMA0) is used to modulate a RFM22B in direct-asynchronous mode. I expect other transmitters could probably be used (i.e. NTX2's or similar) at lower bandwidths.

## Flight History
* v0.1 - First test flight on Horus 37, no FEC. Read more about that here: http://rfhead.net/?p=637
* v0.2 - Second test flight on Horus 39, with LDPC FEC enabled. Read more here: http://www.rowetel.com/?p=5344

![Image downlinked via Wenet on Horus 38](http://rfhead.net/temp/wenet_fec_small.jpeg)
The above image was captured on Horus 38, and downlinked via Wenet.

## Ubuntu 16.04 RX
* There is now a guide on how to set up a RX station using Ubuntu within the INSTALL_ubuntu file

## Dependencies
* Python (2.7, though 3 might work with some small mods)
* SSDV (https://github.com/fsphil/ssdv). The `ssdv` binary needs to be available on the PATH.
* crcmod (`pip install crcmod`)
* python requests (install using pip)
* numpy (for debug output tests): `apt-get install python-numpy`
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
* `rx_tester.py` produces a stream of packets on stdout, as would be received from the fsk_demod modem. 
 * Run `python rx_tester.py | python rx_ssdv.py` to feed these test packets into the command-line ssdv rx script.
 * add `--partialupdate N` to the above command to have rx_gui.py update every N received packets.

## Sending/Receiving Images
### TX Side
* The LDPC encoder library needs ldpc_enc.c compiled to a shared library. Run: `gcc -fPIC -shared -o ldpc_enc.so ldpc_enc.c` to do this.
* Run either `python tx_picam.py` (might need sudo to access camera & SPI) or `python tx_test_images.py` on the transmitter Raspberry Pi. There's also a start_tx.sh bash script which also sets up a RFM22B. I run this bash script from /etc/rc.local so it starts on boot.

#### IMPORTANT NOTES
* While the transit code requests an output baud rate of 115200 baud from the RPi's UART, the acheived baud rate (due to clock divisors) is actually 115386.843 baud (measured using a frequency counter). All of the resampling within the receive chain had to be adjusted accordingly, which means CPU-intensive fractional decimators.
* Apparently the newer Raspberry Pi's (or possibly just a newer version of Raspbian) use the alternate UART hardware by default, which has a smaller transmit buffer. This may result in gaps between bytes, which will likely throw the rx timing estimation off.

### RX Side
* NOTE: On Ubuntu 16.04 or newer, follow the guide within INSTALL_ubuntu

To be able to run a full receive chain, from SDR through to images, you'll need:
* GnuRadio + libraries for whatever SDR you plan on using.
* `fsk_demod`, `drs232_ldpc`, 'tsrc' from codec2-dev. You can get these using
 * `svn checkout http://svn.code.sf.net/p/freetel/code/codec2-dev/`
 * Note that codec2 needs speex and libsamplerate libraries. You can get these using: `apt-get install speed-* libsamplerate0-dev`
 * `cd codec2-dev && mkdir build-linux && cd build-linux && cmake ../`
 * Go back to the main codec2-dev directory and:
 * Build `drs232_ldpc` (the packet de-framer & FEC) using `gcc src/drs232_ldpc.c src/mpdecode_core.c -o src/drs232_ldpc -Wall -lm`
 * Build 'tsrc' (the fractional resampler) using `gcc unittest/tsrc.c -o unittest/tsrc -lm -lsamplerate`
 * Then copy `build-linux/src/fsk_demod`, `src/drs232_ldpc`, `unittest/tsrc` and `octave/fskdemodgui.py` to this (wenet) directory. 

* A few example gnuradio-companion flow-graphs are in the `grc` directory, for different SDRs. These receive samples from the SDR, demodulate a 500KHz section of spectrum as USB, resamples them to fsbaud*8 (which fsk_demod requires), then presents these samples via a TCP sink, which is acting as a TCP server. You will probably need to modify these to set the appropriate receive frequency.

* To receive the FSK data and display the images 'live', run:
 * In another terminal: `python rx_gui.py`, which will listen via UDP for new images to display.
 * Start the appropriate GNURadio Companion Flowgraph. This will start listening on TCP port 9898. The GUI will not open until... 
 * Start the FSK modem with:
  * `nc localhost 9898 | ./fsk_demod 2XS 8 923096 115387 - - S 2> >(python fskdemodgui.py) | ./drs232_ldpc - - -vv| python rx_ssdv.py --partialupdate 16`

### RX Without GNURadio
It's possible to use csdr (Get it from https://github.com/simonyiszk/csdr ) to perform the sideband demodulation. 

Example (RTLSDR):
`rtl_sdr -s 923096 -f 440980000 -g 35 - | csdr convert_u8_f | csdr bandpass_fir_fft_cc 0.05 0.45 0.05 | csdr realpart_cf | csdr gain_ff 0.5 | csdr convert_f_s16 | ./fsk_demod 2XS 8 923096 115387 - - S 2> >(python fskdemodgui.py) | ./drs232_ldpc - - -vv| python rx_ssdv.py --partialupdate 16`

This mess of a command line (bash piping, yay!) receives samples from the rtlsdr, filters out the upper 'sideband' of the received bandwidth, then throws away the imaginary part and convert to 16-bit shorts. The signal is then fed into fsk_demod (the FSK modem). Debug output (on stderr) from the modem is piped into a python GUI), while the received soft-decision 'bits' are piped into drs232_ldpc, which does de-framing and LDPC error correction. Packets which pass checksum are then passed onto the rx_ssdv.py python utility for assembly into images.

On my flights the centre frequency of the transmitter is around 441.2 MHz, so I tune the RTLSDR to just below 441 MHz to sit the signal roughly in the middle of the passband.

It should be quite possible to use other SDRs (i.e. the AirSpy) with appropriate tweaking of the filter and source sample type conversion parameters. 

## RX Tips.
* It is highly recommended to use a preamplifier in front of your RTLSDR to lower the overall noise figure of the system. With a NooElec RTLSDR (R820T2 Tuner) and a [HabAmp](https://store.uputronics.com/index.php?route=product/product&product_id=53), we were able to acheive a Minimum-Detectable-Signal (MDS - which we defined as the point where we get no packet errors) of around -112 dBm.
* If needed, the transmit bitrate can be slowed down by editing the defaults in tx_picam.py. You will then have to determine the appropriate parameters for fsk_demod and the preceding filtering/resampling chain.


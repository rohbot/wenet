#!/bin/bash
#
#	Start RX using an Airspy.
#
python rx_gui.py &
airspy_rx -f441.0 -r /dev/stdout -a 1 -h 21 | csdr convert_s16_f | csdr bandpass_fir_fft_cc 0.025 0.175 0.025 | csdr fractional_decimator_ff 2.708277 | csdr realpart_cf | csdr convert_f_s16 | ./fsk_demod 2X 8 923096 115387 - - S 2> >(python fskdemodgui.py) | ./drs232 - - | python rx_ssdv.py --partialupdate 16
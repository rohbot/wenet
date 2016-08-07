#!/bin/bash
#
#	Start RX using a rtlsdr.
#
python rx_gui.py &
rtl_sdr -s 1000000 -f 441000000 -g 35 - | csdr convert_u8_f | csdr bandpass_fir_fft_cc 0.1 0.4 0.05 | csdr fractional_decimator_ff 1.08331 | csdr realpart_cf | csdr convert_f_s16 | ./fsk_demod 2X 8 923096 115387 - - S 2> >(python fskdemodgui.py --wide) | ./drs232 - - | python rx_ssdv.py --partialupdate 16
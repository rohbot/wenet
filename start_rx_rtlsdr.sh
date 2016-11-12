#!/bin/bash
#
#	Start RX using a rtlsdr.
#
python rx_gui.py &
rtl_sdr -s 1000000 -f 440980000 -g 35 - | csdr convert_u8_f | csdr bandpass_fir_fft_cc 0.05 0.45 0.05 | csdr realpart_cf | csdr gain_ff 0.5 | csdr convert_f_s16 | ./tsrc - - 0.9230968 | ./fsk_demod 2XS 8 923096 115387 - - S 2> >(python fskdemodgui.py --wide) | ./drs232_ldpc - -  -vv| python rx_ssdv.py --partialupdate 16

#!/bin/bash
#
#	Wenet RX-side Initialisation Script
#	2016-12-05 Mark Jessop <vk5qi@rfhead.net>
#
#	This assumes an RTLSDR will be used for RX.
#

# Set CHANGEME to your callsign.
MYCALL=CHANGEME

# Change the following path as appropriate.
# If running this from a .desktop file, you may need to set an absolute path here
# i.e. /home/username/wenet/rx/
cd ~/wenet/rx/

# Start up the SSDV Uploader script and push it into the background.
python ssdv_upload.py $MYCALL &

# Start the SSDV RX GUI.
python rx_gui.py &

# Uncomment the following line if using a V3 RTLSDR and need the Bias-Tee enabled.
# rtl_biast -b 1 

# Start up the receive chain. 
rtl_sdr -s 923096 -f 440980000 -g 35 - | csdr convert_u8_f | \
csdr bandpass_fir_fft_cc 0.05 0.45 0.05 | csdr realpart_cf | \
csdr gain_ff 0.5 | csdr convert_f_s16 | \
./fsk_demod 2XS 8 923096 115387 - - S 2> >(python fskdemodgui.py --wide) | \
./drs232_ldpc - -  -vv | \
python rx_ssdv.py --partialupdate 16

#!/bin/bash
#
#	Wenet RX-side Initialisation Script
#	2018-12-20 Mark Jessop <vk5qi@rfhead.net>
#
#	This assumes an RTLSDR will be used for RX.
#

# Set CHANGEME to your callsign.
MYCALL=CHANGEME

# Wenet Transmission Centre Frequency:

# Default Wenet Frequency, as used on most Project Horus flights.
RXFREQ=441200000
# Secondary downlink frequency, used on dual-launch flights
#RXFREQ=443500000

# Receiver Gain. Set this to 0 to use automatic gain control, otherwise if running a
# preamplifier, you may want to experiment with different gain settings to optimize
# your receiver setup.
# You can find what gain range is valid for your RTLSDR by running: rtl_test
GAIN=0

# Bias Tee Enable (1) or Disable (0)
BIAS=0
# Note that this will need the rtl_biast utility available, which means
# building the rtl-sdr utils from this repo: https://github.com/rtlsdrblog/rtl-sdr


# Change the following path as appropriate.
# If running this from a .desktop file, you may need to set an absolute path here
# i.e. /home/username/wenet/rx/
cd ~/wenet/rx/




# Receive Flow Type:
# IQ = Pass complex samples into the fsk demodulator. (Default)
#      This is suitable for use with RTLSDRs that do not have DC bias issues.
#      Examples: RTLSDR-Blog v3 Dongles. (anything with a R820T or R820T2 tuner)
#
# SSB = Demodulate the IQ from the SDR as a very wide (400 kHz) USB signal, and
#       pass that into the fsk demodulator.
#       This is useful when the RTLSDR has a DC bias that may affect demodulation.
#		i.e. RTLSDRs with Elonics E4000 or FitiPower FC0013 tuners.
#		Note: This requires that the csdr utility be installed: https://github.com/simonyiszk/csdr.git
RX_FLOW=IQ




#
# Modem Settings - Don't adjust these unless you really need to!
#
BAUD_RATE=115177 # Baud rate, in symbols/second.
OVERSAMPLING=8	 # FSK Demod Oversampling rate. 8X oversampling works best for 115k FSK

#
# Main Script Start... Don't edit anything below this unless you know what you're doing!
#

# Start up the SSDV Uploader script and push it into the background.
python ssdv_upload.py $MYCALL &
SSDV_UPLOAD_PID=$!
# Start the SSDV RX GUI.
python rx_gui.py &
# Start the Telemetry GUI.
python TelemetryGUI.py $MYCALL &


# Calculate the SDR sample rate required.
SDR_RATE=$(($BAUD_RATE * $OVERSAMPLING))
# Calculate the SDR centre frequency. 
# The fsk_demod acquisition window is from Rs/2 to Fs/2 - Rs.
# Given Fs is Rs * Os  (Os = oversampling), we can calculate the required tuning offset with the equation:
# Offset = Fcenter - Rs*(Os/4 - 0.25)
RX_SSB_FREQ=$(echo "$RXFREQ - $BAUD_RATE * ($OVERSAMPLING/4 - 0.25)" | bc)

echo "Using SDR Sample Rate: $SDR_RATE Hz"
echo "Using SDR Centre Frequency: $RX_SSB_FREQ Hz"

if [ "$BIAS" = "1" ]; then
	echo "Enabling Bias Tee"
	rtl_biast -b 1 
fi

# Start up the receive chain.
if [ "$RX_FLOW" = "IQ" ]; then
	# If we have a RTLSDR that receives using a low-IF, then we have no DC spike issues,
	# and can feed complex samples straight into the fsk demodulator.
    echo "Using Complex Samples."

	rtl_sdr -s $SDR_RATE -f $RX_SSB_FREQ -g $GAIN - | \
	./fsk_demod --cu8 -s --stats=100 2 $SDR_RATE $BAUD_RATE - - 2> >(python fskdemodgui.py --wide) | \
	./drs232_ldpc - -  -vv | \
	python rx_ssdv.py --partialupdate 16
else
	# If using a RTLSDR that has a DC spike (i.e. either has a FitiPower FC0012 or Elonics E4000 Tuner),
	# we receive below the centre frequency, and perform USB demodulation.
	echo "Using Real Samples and USB demodulation."

	rtl_sdr -s $SDR_RATE -f $RX_SSB_FREQ -g $GAIN - | csdr convert_u8_f | \
	csdr bandpass_fir_fft_cc 0.05 0.45 0.05 | csdr realpart_cf | \
	csdr gain_ff 0.5 | csdr convert_f_s16 | \
	./fsk_demod -s --stats=100 2 $SDR_RATE $BAUD_RATE - - 2> >(python fskdemodgui.py --wide) | \
	./drs232_ldpc - -  -vv | \
	python rx_ssdv.py --partialupdate 16

fi

# Kill off the SSDV Uploader (since that has no GUI and we can't easily close it)
kill $SSDV_UPLOAD_PID
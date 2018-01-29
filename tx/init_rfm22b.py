#!/usr/bin/env python
#
#	RFM22B Initialisation for Horus High Speed Telemetry
#
#	Copyright (C) 2018  Mark Jessop <vk5qi@rfhead.net>
#	Released under GNU GPL v3 or later
#
#	A mash together of a few different libraries, including:
#		https://github.com/MaxBaex/raspi_rfm22
#		https://github.com/omcaree/rfm22b/blob/master/src/rfm22b.cpp
#
#	Uses spidev for SPI comms.
#
#	Note: This is fairly limited, and was only intended to get a RFM22B
#	into direct-async TX mode.
#	Lots of functions (i.e. anything to do with packets) are unimplemented.
#
#	Electrical Connections:
#		GPIO0 <-> TX_ANT
#		GPIO1 <-> RX_ANT
#		SDN <-> GND (Not sure if this is a good thing, not being about to hard reset it..)
#		GPIO2 <-> UART TXD (for direct mode TX)
#		SPI - connected to CE1 (can change this when instantiating the object.)
#

import spidev, sys, time

class REG:
	DEVICE_TYPE                           = 0x00
	DEVICE_VERSION                        = 0x01
	DEVICE_STATUS                         = 0x02
	INTERRUPT_STATUS_1                    = 0x03
	INTERRUPT_STATUS_2                    = 0x04
	INTERRUPT_ENABLE_1                    = 0x05
	INTERRUPT_ENABLE_2                    = 0x06
	OPERATING_FUNCTION_CONTROL_1          = 0x07
	OPERATING_FUNCTION_CONTROL_2          = 0x08
	CRYSTAL_OSCILLATOR_LOAD               = 0x09
	MICROCONTROLLER_CLOCK_OUTPUT          = 0x0A
	GPIO0_CONFIGURATION                   = 0x0B
	GPIO1_CONFIGURATION                   = 0x0C
	GPIO2_CONFIGURATION                   = 0x0D
	I_O_PORT_CONFIGURATION                = 0x0E
	ADC_CONFIGURATION                     = 0x0F
	ADC_SENSOR_AMPLIFIER_OFFSET           = 0x10
	ADC_VALUE                             = 0x11
	TEMPERATURE_SENSOR_CONTROL            = 0x12
	TEMPERATURE_VALUE_OFFSET              = 0x13
	WAKE_UP_TIMER_PERIOD_1                = 0x14
	WAKE_UP_TIMER_PERIOD_2                = 0x15
	WAKE_UP_TIMER_PERIOD_3                = 0x16
	WAKE_UP_TIMER_VALUE_1                 = 0x17
	WAKE_UP_TIMER_VALUE_2                 = 0x18
	LOW_DUTY_CYCLE_MODE_DURATION          = 0x19
	LOW_BATTERY_DETECTION_THRESHOLD       = 0x1A
	BATTERY_VOLTAGE_LEVEL                 = 0x1B
	IF_FILTER_BANDWIDTH                   = 0x1C
	AFC_LOOP_GEARSHIFT_OVERRIDE           = 0x1D
	AFC_TIMING_CONTROL                    = 0x1E
	CLOCK_RECOVERY_GEARSHIFT_OVERRIDE     = 0x1F
	CLOCK_RECOVERY_OVERSAMPLING_RATIO     = 0x20
	CLOCK_RECOVERY_OFFSET_2               = 0x21
	CLOCK_RECOVERY_OFFSET_1               = 0x22
	CLOCK_RECOVERY_OFFSET_0               = 0x23
	CLOCK_RECOVERY_TIMING_LOOP_GAIN_1     = 0x24
	CLOCK_RECOVERY_TIMING_LOOP_GAIN_0     = 0x25
	RECEIVED_SIGNAL_STRENGTH_INDICATOR    = 0x26
	RSSI_THRESSHOLF_FOR_CLEAR_CHANNEL_INDICATOR = 0x27
	ANTENNA_DIVERSITY_REGISTER_1          = 0x28
	ANTENNA_DIVERSITY_REGISTER_2          = 0x29
	AFC_LIMITER                           = 0x2A
	AFC_CORRECTION_READ                   = 0x2B
	OOK_COUNTER_VALUE_1                   = 0x2C
	OOK_COUNTER_VALUE_2                   = 0x2D
	SLICER_PEAK_HOLD                      = 0x2E
	# Register 0x2F reserved
	DATA_ACCESS_CONTROL                   = 0x30
	EzMAC_STATUS                          = 0x31
	HEADER_CONTROL_1                      = 0x32
	HEADER_CONTROL_2                      = 0x33
	PREAMBLE_LENGTH                       = 0x34
	PREAMBLE_DETECTION_CONTROL            = 0x35
	SYNC_WORD_3                           = 0x36
	SYNC_WORD_2                           = 0x37
	SYNC_WORD_1                           = 0x38
	SYNC_WORD_0                           = 0x39
	TRANSMIT_HEADER_3                     = 0x3A
	TRANSMIT_HEADER_2                     = 0x3B
	TRANSMIT_HEADER_1                     = 0x3C
	TRANSMIT_HEADER_0                     = 0x3D
	TRANSMIT_PACKET_LENGTH                = 0x3E
	CHECK_HEADER_3                        = 0x3F
	CHECK_HEADER_2                        = 0x40
	CHECK_HEADER_1                        = 0x41
	CHECK_HEADER_0                        = 0x42
	HEADER_ENABLE_3                       = 0x43
	HEADER_ENABLE_2                       = 0x44
	HEADER_ENABLE_1                       = 0x45
	HEADER_ENABLE_0                       = 0x46
	RECEIVED_HEADER_3                     = 0x47
	RECEIVED_HEADER_2                     = 0x48
	RECEIVED_HEADER_1                     = 0x49
	RECEIVED_HEADER_0                     = 0x4A
	RECEIVED_PACKET_LENGTH                = 0x4B
	# Registers 0x4C-4E reserved
	ADC8_CONTROL                          = 0x4F
	# Registers 0x50-5F reserved
	CHANNEL_FILTER_COEFFICIENT_ADDRESS    = 0x60
	# Register 0x61 reserved
	CRYSTAL_OSCILLATOR_CONTROL_TEST       = 0x62
	# Registers 0x63-68 reserved
	AGC_OVERRIDE_1                        = 0x69
	# Registers 0x6A-0x6C reserved
	TX_POWER                              = 0x6D
	TX_DATA_RATE_1                        = 0x6E
	TX_DATA_RATE_0                        = 0x6F
	MODULATION_MODE_CONTROL_1             = 0x70
	MODULATION_MODE_CONTROL_2             = 0x71
	FREQUENCY_DEVIATION                   = 0x72
	FREQUENCY_OFFSET_1                    = 0x73
	FREQUENCY_OFFSET_2                    = 0x74
	FREQUENCY_BAND_SELECT                 = 0x75
	NOMINAL_CARRIER_FREQUENCY_1           = 0x76
	NOMINAL_CARRIER_FREQUENCY_0           = 0x77
	# Register 0x78 reserved
	FREQUENCY_HOPPING_CHANNEL_SELECT      = 0x79
	FREQUENCY_HOPPING_STEP_SIZE           = 0x7A
	# Register 0x7B reserved
	TX_FIFO_CONTROL_1                     = 0x7C
	TX_FIFO_CONTROL_2                     = 0x7D
	RX_FIFO_CONTROL                       = 0x7E
	FIFO_ACCESS                           = 0x7F

class MODE:
	IDLE = 0
	RX = 1
	TX = 2

class TXPOW:
	TXPOW_1DBM                        = 0x00
	TXPOW_2DBM                        = 0x01
	TXPOW_5DBM                        = 0x02
	TXPOW_8DBM                        = 0x03
	TXPOW_11DBM                       = 0x04
	TXPOW_14DBM                       = 0x05
	TXPOW_17DBM                       = 0x06
	TXPOW_20DBM                       = 0x07

class CONFIGS:
# Register:         1c,   1f,   20,   21,   22,   23,   24,   25,   2c,   2d,   2e,   58,   69,   6e,   6f,   70,   71,   72
	REGISTERS = [0x1C,0x1F,0x20,0x21,0x22,0x23,0x24,0x25,0x2C,0x2D,0x2E,0x58,0x69,0x6E,0x6F,0x70,0x71,0x72]
	DIRECT_120K = [0x8a, 0x03, 0x60, 0x01, 0x55, 0x55, 0x02, 0xad, 0x40, 0x0a, 0x50, 0x80, 0x60, 0x20, 0x00, 0x00, 0x02, 0x60]

class RFM22B(object):

	def __init__(self,device=1):
		self.spi = spidev.SpiDev()
		self.spi.open(0,device)
		self.spi.max_speed_hz = 1000000

		if not self.check_connection():
			print("Init Failed!")
			self.spi.close()
			sys.exit(1)

		self.setup_basic()

		print("Init Complete!")

	def close(self):
		self.spi.close()

	def read_register(self,address):
		return self.spi.xfer([address,0])[1]

	def write_register(self,address,data):
		return self.spi.xfer([address | 0x80, data])

	def check_connection(self):
		device_type = self.read_register(REG.DEVICE_TYPE)
		device_version = self.read_register(REG.DEVICE_VERSION)

		print("Device Type:\t %d" % device_type)
		print("Device Version:\t %d" % device_version)

		if (device_type != 8) or (device_version != 6):
			print("Wrong Device?!")
			return False 
		else:
			return True 
# 441.2E6 = HBSEL: 0 FB: 20 FBS: 84 FC: 7679 NCF1: 29, NCF0: 255
	def set_frequency(self, freq_hz):
		if (freq_hz<240E6) or (freq_hz>960E6):
			print("Invalid Frequency!")
			return False

		hbsel = 1 if (freq_hz>= 480E6) else 0

		fb = int(freq_hz/10E6/(hbsel+1) - 24)
		fbs = (1<<6) | (hbsel<<5) | fb
		fc = int((freq_hz/(10.0E6 * (hbsel+1)) - fb - 24) * 64000)

		ncf1 = fc>>8
		ncf0 = fc & 0xFF

		print("hbsel: %d, fb: %d, fbs: %d, fc: %d, ncf1: %d, ncf0: %d" % (hbsel,fb,fbs,fc,ncf1,ncf0)) 

		self.write_register(REG.FREQUENCY_BAND_SELECT,fbs)
		self.write_register(REG.NOMINAL_CARRIER_FREQUENCY_1,ncf1)
		self.write_register(REG.NOMINAL_CARRIER_FREQUENCY_0,ncf0)

		# Read back registers.
		fbs_read = self.read_register(REG.FREQUENCY_BAND_SELECT)
		ncf1_read = self.read_register(REG.NOMINAL_CARRIER_FREQUENCY_1)
		ncf0_read = self.read_register(REG.NOMINAL_CARRIER_FREQUENCY_0)

		if (fbs == fbs_read) and (ncf1 == ncf1_read) and (ncf0 == ncf0_read):
			print("Frequency set OK!")
			return True
		else:
			print("Frequency not set correctly!")
			return False

	def setup_basic(self):
		# Software reset.
		self.write_register(REG.OPERATING_FUNCTION_CONTROL_1,0x80)
		time.sleep(0.1)
		# Interrupts
		self.write_register(REG.INTERRUPT_ENABLE_1,0x87)
		# Switch to ready mode.
		self.write_register(REG.OPERATING_FUNCTION_CONTROL_1,0x01)
		self.write_register(REG.CRYSTAL_OSCILLATOR_LOAD,0x7f)
		# Configure GPIO 0 and 1 settings.
		self.write_register(REG.GPIO0_CONFIGURATION, 0x12) # TX State, physically wired into TX_ANT pin.
		self.write_register(REG.GPIO1_CONFIGURATION, 0x15) # RX State, physically wired into RX_ANT pin.
	
	# Program a bulk set of registers. 
	# I'm using this to set a bunch of different registers at one time, to load up pre-calculated configs.
	def set_bulk(self,registers,data):
		if len(registers) != len(data):
			print("Array length mismatch!")
			return False

		for k in xrange(len(registers)):
			self.write_register(registers[k],data[k])

	def set_tx_power(self,power):
		self.write_register(REG.TX_POWER,power)

	def set_mode(self,mode):
		self.write_register(REG.OPERATING_FUNCTION_CONTROL_1,mode)

if __name__ == '__main__':

	# Attempt to extract a frequency from the first argument:
	if len(sys.argv)<2:
		print("Usage: \tpython init_rfm22b.py <TX Frequency in MHz>")
		print("Example: \tpython init_rfm22b.py 441.200")
		sys.exit(1)

	try:
		tx_freq = float(sys.argv[1])
	except:
		print("Unable to parse input.")

	if tx_freq>450.0 or tx_freq<430.00:
		print("Frequency out of 70cm band, using default.")
		tx_freq = 441.200*1e6
	else:
		tx_freq = tx_freq*1e6

	rfm = RFM22B()
	rfm.set_tx_power(TXPOW.TXPOW_17DBM | 0x08)
	rfm.set_frequency(tx_freq)
	rfm.write_register(REG.GPIO2_CONFIGURATION,0x30) # TX Data In
	rfm.set_bulk(CONFIGS.REGISTERS,CONFIGS.DIRECT_120K) # Direct Asynchronous mode, ~120KHz tone spacing.
	rfm.set_mode(0x09)
	rfm.close()


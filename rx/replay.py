#!/usr/bin/env python
import sys, os.path, time

if len(sys.argv) != 3:
	print("USAGE: python replay.py <samplerate> filename.bin")

file_name = sys.argv[2]
sample_rate = int(sys.argv[1])

if not os.path.exists(file_name):
	print("File does not exist.")
	sys.exit(0)

file_size = os.path.getsize(file_name)

block_size = sample_rate/10

f = open(file_name, 'rb')

while file_size > 0:
	if file_size > block_size:
		samples = f.read(block_size)
		file_size -= block_size
	else:
		samples = f.read()

	sys.stdout.write(samples)
	time.sleep(0.1)

f.close()


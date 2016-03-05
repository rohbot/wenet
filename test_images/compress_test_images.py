#!/usr/bin/env python
#
# Quick script to resize and SSDV-compress a selection of test images.
# Original resolution: 1488x1120
#	800x600
#	640x480
#	320x240
#
#	Requires:
#		Imagemagick
#		ssdv (https://github.com/fsphil/ssdv)

import os, glob

# images should be named 1.jpg, 2.jpg, etc.
image_numbers = xrange(1,14)
new_sizes = ["800x608","640x480","320x240"]
callsign = "VK5QI"

# Resize images.
for x in image_numbers:
	# make a copy of the raw image.
	os.system("cp %d.jpg %d_raw.jpg" % (x,x))
	# Produce resized images.

	for size in new_sizes:
		os.system("convert %d.jpg -resize %s\! %d_%s.jpg" % (x,size,x,size))

# Compress with SSDV.
new_sizes.append("raw")

for x in image_numbers:
	for size in new_sizes:
		os.system("ssdv -e -c %s -i %d %d_%s.jpg %d_%s.ssdv" % (callsign,x,x,size,x,size))

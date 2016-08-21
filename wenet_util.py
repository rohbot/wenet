#!/usr/bin/env python
#
#	Wenet Utility Functions
#

import os,glob
from PacketTX import write_debug_message

#
# PiCam Wrapper Functions 
#

# Adjust this line to suit your needs (resolution, image flip, etc)
picam_str = "raspistill -t 3000 -ex auto -mm matrix -o %s -vf -hf -w 2592 -h 1936"
temp_file_prefix = "./temp_pic"


def capture_single(filename="temp.jpg"):
	os.system(picam_str % filename)

def capture_multiple(filename="output.jpg", n=5, temp_prefix=temp_file_prefix):
	# Remove any existing temporary images
	os.system("rm %s*.jpg"%temp_prefix)

	# Capture n images
	for pic_num in range(n):
		write_debug_message("Capturing Image %d of %d..." % (pic_num, n))
		capture_single("%s_%d.jpg"%(temp_prefix,pic_num))

	# Super high-tech image quality recognition filter
	# (pick the largest image... thanks daveake!)
	write_debug_message("Choosing Best Image...")
	pic_list = glob.glob("%s*.jpg"%temp_prefix)
	pic_sizes = []
	for pic in pic_list:
		pic_sizes.append(os.path.getsize(pic))
	largest_pic = pic_list[pic_sizes.index(max(pic_sizes))]

	# Copy best image to resultant filename.
	os.system("cp %s %s" % (largest_pic, filename))

	# Remove temporary images
	os.system("rm %s*.jpg"%temp_prefix)

if __name__ == "__main__":
	capture_multiple()

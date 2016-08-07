#!/usr/bin/env python
#
#	PiCam Wrapper Functions
#

import os,glob

picam_str = "raspistill -t 100 -ex auto -o %s -vf -hf -w 1600 -h 1200"
temp_file_prefix = "./temp_pic"


def capture_single(filename="temp.jpg"):
	os.system(picam_str % filename)

def capture_multiple(filename="output.jpg", n=10, temp_prefix=temp_file_prefix):
	# Remove any existing temporary images
	os.system("rm %s*.jpg"%temp_prefix)

	# Capture n images
	for pic_num in range(n):
		capture_single("%s_%d.jpg"%(temp_prefix,pic_num))

	# Super high-tech image quality recognition filter
	# (pick the largest image... thanks daveake!)
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

#!/usr/bin/env python
#
# A naive solution for Instagram puzzle,
# http://instagram-engineering.tumblr.com/post/12651721845/instagram-engineering-challenge-the-unshredder
#
# Copyright 2011 Nicolas Remond
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from PIL import Image
import sys

from math import sqrt,log, floor


# shred configuration
nb_shreds_min = 4
nb_shreds_max = 50

# matching configuration
threshold = 0.09
window_size = 5

# Do not change from here
surround = (window_size - 1) / 2
f_window = float(surround*2 + 1)

def calculate_difference(v1, v2):
	differences = 0.0
	for i in xrange(surround, len(v1)-surround, max(surround/2,1)):	
		sum_squared_differences  = 0.0
		for channel in [0, 1, 2]:
			chan1 = sum(map(lambda x: x[channel], v1[i-surround:i+surround])) / f_window
			chan2 = sum(map(lambda x: x[channel], v2[i-surround:i+surround])) / f_window
			chan1 /= 255.0
			chan2 /= 255.0
			
			diff = (log(chan1 + 1.0, 2) - log(chan2 + 1.0, 2))**2
			sum_squared_differences += diff
		sum_differences = sqrt(sum_squared_differences)
		if sum_differences  > threshold:
			differences += 1
		
	return differences

	
class Shred(object):
	def __init__(self, image):
		self.image = image
		data = image.getdata() # This gets pixel data
		width, height = image.size
		self.left_vector = [data[y * width] for y in range(0, height)]
		self.right_vector = [data[y * width + (width-1)] for y in range(0, height)]		

	def _match(self, vref, vectors):
		distances = [calculate_difference(vref, v) for v in vectors]
		return min(enumerate(distances), key=lambda (i, v) : v)

	def match_left(self, shreds):
		return self._match(self.left_vector, [s.right_vector for s in shreds])
	
	def match_right(self, shreds):
		return self._match(self.right_vector, [s.left_vector for s in shreds])


class ProgressBar(object):
	def __init__(self, total, prefix=""):
		self.total = float(total)
		self.width = 50 # width defines bar width
		self.prefix = prefix

	# percent defines current percentage
	def update(self, amount):
		percent = float(amount) / self.total *100.0
		marks = floor(self.width * (percent / 100.0))
		spaces = floor(self.width - marks)

		loader = self.prefix + '[' + ('=' * int(marks)) + (' ' * int(spaces)) + ']'

		sys.stdout.write("%s %d%%\r" % (loader, percent))
		if percent >= 100:
			sys.stdout.write("\n")
		sys.stdout.flush()
 
def guess_nb_shreds(image): 
	width, height = image.size
	data = image.getdata() # This gets pixel data
	
	progress_bar = ProgressBar(nb_shreds_max-nb_shreds_min-1, "N. of shreds: ")
	
	nb_columns = 0
	max_score_difference = 0.0
	for nb_columns_current in xrange(nb_shreds_min, nb_shreds_max):
		shred_width = width / nb_columns_current
	
		# only consider shreds width that can divide correctly the image
		if width % shred_width != 0:
			progress_bar.update(nb_columns_current - nb_shreds_min)
			continue
		
		# compute the difference score between all shreds
		score_difference = 0.0
		for shred_number in xrange(1, nb_columns_current-1):
			x1 = shred_width*shred_number - 1
			x2 = x1 + 1
			v1 = [data[x1 + y*width] for y in range(0, height)]
			v2 = [data[x2 + y*width] for y in range(0, height)]	
			score_difference += calculate_difference(v1, v2)

		score_difference /= float(width / shred_width)
		
		# When we are on a edge between two sherds, the difference is maximum
		if score_difference > max_score_difference:
			max_score_difference = score_difference
			nb_columns = nb_columns_current
		
		progress_bar.update(nb_columns_current - nb_shreds_min)
		
		
	print "Considering that there are %i shreds" % nb_columns
	return nb_columns
		
		
def main(argv):
	if len(argv) != 3 :
		print 'Usage: unshredder.py <input_image> <output_image>'
		exit(0)

	input_filename = argv[1]
	output_filename = argv[2]
	image = Image.open(input_filename)
	width, height = image.size

	number_of_columns = guess_nb_shreds(image)
	shred_width = width / number_of_columns

	shreds = []
	for shred_number in xrange(0,number_of_columns):
		x1, y1 = shred_width * shred_number, 0
		x2, y2 = x1 + shred_width, height
		source_region = image.crop((x1, y1, x2, y2))
		shreds.append(Shred(source_region))
	

	print 
	progress_bar = ProgressBar(len(shreds), "Unshredding:  ")
	
	# start to reconstruct the image with a random shred
	ordered_shreds = [shreds.pop()]
	while len(shreds) > 0:
		# we try to find the best match of the left and the right side
		# of the already reconstructed part
		(i_left, min_left) = ordered_shreds[0].match_left(shreds)
		(i_right, min_right) = ordered_shreds[-1].match_right(shreds)
		
		# we choose to add the best fit
		if min_left < min_right :
			ordered_shreds.insert(0, shreds.pop(i_left))
		else :
			ordered_shreds.append(shreds.pop(i_right))
		
		progress_bar.update(len(ordered_shreds))
		
	#build the unshredded image
	unshredded = Image.new('RGBA', image.size)
	for (shred_number, shred)in enumerate(ordered_shreds):
		destination_point = (shred_width * shred_number, 0)
		unshredded.paste(shred.image, destination_point)
	
	# Output the new image
	unshredded.save(output_filename)
	print "Output image file saved, %s" % output_filename

if __name__ == "__main__":
    main(sys.argv)			
			


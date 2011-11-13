#!/usr/bin/env python

from PIL import Image
import sys


def calculate_difference(vector_one, vector_two):
	""" Given two vectors of pixels in RGBA format, we calculate how
		different the two columns are. We do this by treating the column
		as a vector of 3*n space where n is the number of rows in the
		image. It's 3x because we treat red, green, and blue channels 
		as individual dimensions in the vector. We use a simple euclidean
		distance measure as the difference. Note that we calculate the
		distance in log space to emphasize the difference between
		non-highlight colors. """

	from math import sqrt, log
	sum_squared_differences = 0.0
	for (pixel1,pixel2) in zip(vector_one, vector_two):
		sum_line = 0.0
		for (chan1,chan2) in zip(pixel1, pixel2):
			diff_squared = (log((chan1 + 1.0) / 256.0, 10) - log((chan2 + 1.0) / 256.0, 10))**2
			sum_squared_differences += diff_squared
			
		#sum_squared_differences += sqrt(sum_line)
			
	return sum_squared_differences

class Shred(object):
	def __init__(self, image):
		self.image = image
		
		data = image.getdata() # This gets pixel data
		width, height = image.size
		self.left_vector = [data[y * width] for y in range(0, height)]
		self.right_vector = [data[y * width + (width-1)] for y in range(0, height)]		

	def match_left(self, shreds):
		distances = [calculate_difference(self.left_vector, v.right_vector) for v in shreds]
		
		print "left distances " +str([v for v in enumerate(distances)])
		
		return min(enumerate(distances), key=lambda (i, v) : v)
	
	def match_right(self, shreds):
		distances = [calculate_difference(self.right_vector, v.left_vector) for v in shreds]
		
		print "right distances " +str([v for v in enumerate(distances)])
		return min(enumerate(distances), key=lambda (i, v) : v) 
	 

def main(argv):
	if len(argv) != 2 :
		print argv[0] + " takes exactly 1 arguments"
		exit(0)

	input_filename = argv[1]
	image = Image.open(input_filename)
	width, height = image.size

	
	NUMBER_OF_COLUMNS = 20
	shred_width = width / NUMBER_OF_COLUMNS
	
	shreds = []
	for shred_number in range(0,NUMBER_OF_COLUMNS):
		x1, y1 = shred_width * shred_number, 0
		x2, y2 = x1 + shred_width, height
		source_region = image.crop((x1, y1, x2, y2))
		shreds.append(Shred(source_region))
	
	
	#print width, height
	#print shreds[0].image.size
	#print len(shreds[0].left_vector)
	#print  (shreds[0].left_vector)


	ordered_shreds = []
	ordered_shreds.append(shreds.pop())
	while len(shreds) > 0:
	#for i in xrange(1):
		(i_left, max_left) = ordered_shreds[0].match_left(shreds)
		print "MAX LEFT :",
		print  (i_left, max_left) 
		(i_right, max_right) = ordered_shreds[-1].match_right(shreds)
		print "MAX RIGHT :",
		print (i_right, max_right)
		
		
		if max_left > max_right :
			ordered_shreds.insert(0, shreds.pop(i_left))
		else :
			ordered_shreds.append(shreds.pop(i_right))
			



	
	
	#build the unshredded image
	unshredded = Image.new('RGBA', image.size)
	for (shred_number, shred)in enumerate(ordered_shreds):
		destination_point = (shred_width * shred_number, 0)
		unshredded.paste(shred.image, destination_point)
	
	# Output the new image
	unshredded.save('unshredded.png', 'png')
	unshredded.show()

if __name__ == "__main__":
    main(sys.argv)			
			


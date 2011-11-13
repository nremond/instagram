#!/usr/bin/env python

from PIL import Image
import sys


def logp(pixel):
	from math import log
	#return log(pixel/255.0 + 1.0, 10)
	return pixel


def calculate_difference(v1, v2):
	#cc
	from math import sqrt
	length = len(v1)
	
	zncc = 0.0
	for channel in [0, 1, 2]:
		sum1 = 0.0
		sum2 = 0.0
		total = 0.0
		
		for i in xrange(2, length-2):
			mean_v1 = sum(map(lambda x: logp(x[channel]), v1[i-2:i+2])) / 5.0
			mean_v2 = sum(map(lambda x: logp(x[channel]), v2[i-2:i+2])) / 5.0
			
			p1 = logp(v1[i][channel]) - mean_v1
			p2 = logp(v2[i][channel]) - mean_v2
			
			total += p1 * p2
			sum1 += (p1) **2
			sum2 += (p2) **2
		zncc += total / sqrt(sum1 * sum2)
	return zncc

def zncc(v1, v2):
	from math import sqrt
	length = len(v1)
	
	zncc = 0.0
	for channel in [0, 1, 2]:
		sum1 = 0.0
		sum2 = 0.0
		total = 0.0
		
		for i in xrange(2, length-2):
			mean_v1 = sum(map(lambda x: logp(x[channel]), v1[i-2:i+2])) / 5.0
			mean_v2 = sum(map(lambda x: logp(x[channel]), v2[i-2:i+2])) / 5.0
			
			p1 = logp(v1[i][channel]) - mean_v1
			p2 = logp(v2[i][channel]) - mean_v2
			
			total += p1 * p2
			sum1 += (p1) **2
			sum2 += (p2) **2
		zncc += total / sqrt(sum1 * sum2)
	return zncc
		
	

def calculate_difference2(vector_one, vector_two):
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
	for pixel in xrange(1, len(vector_one)-1):
		for channel in [0, 1, 2]:
			chan1 = (vector_one[pixel][channel] + vector_one[pixel+1][channel] + vector_one[pixel-1][channel]) / 3.0
			chan2 = (vector_two[pixel][channel] + vector_two[pixel+1][channel] + vector_two[pixel-1][channel]) / 3.0
			#chan1 = vector_one[pixel][channel] / 255.0 
			#chan2 = vector_two[pixel][channel] / 255.0
			
			chan1 /= 255.0
			chan2 /= 255.0
			
			diff_squared = (log(chan1 + 1.0 / 1.0, 10) - log(chan2 + 1.0, 10))**2
			sum_squared_differences += diff_squared
			
	return sum_squared_differences

def _match(vref,vectors):
	distances1 = [calculate_difference(vref, v) for v in vectors]
	distances2 = [calculate_difference(vref[0:-1], v[1:]) for v in vectors]
	distances3 = [calculate_difference(vref[1:], v[0:-1]) for v in vectors]
	
	min1 = min(enumerate(distances1), key=lambda (i, v) : v)
	min2 = min(enumerate(distances2), key=lambda (i, v) : v)
	min3 = min(enumerate(distances3), key=lambda (i, v) : v)
	abs_min = min([min1, min2, min3], key=lambda (i, v) : v)
	print "(m1=%f, i1=%i) "%(min1[1], min1[0]),
	print "(m2=%f, i2=%i) "%(min2[1], min2[0]),
	print "(m3=%f, i3=%i) "%(min3[1], min3[0]),
	print "(abs_m=%f, abs_i=%i) "%(abs_min[1], abs_min[0])
	return abs_min
	#return min1
	
class Shred(object):
	def __init__(self, image):
		self.image = image
		
		data = image.getdata() # This gets pixel data
		width, height = image.size
		self.left_vector = [data[y * width] for y in range(0, height)]
		self.right_vector = [data[y * width + (width-1)] for y in range(0, height)]		

	def match_left(self, shreds):
		return _match(self.left_vector, [s.right_vector for s in shreds])
	
	def match_right(self, shreds):
		return _match(self.right_vector, [s.left_vector for s in shreds])
	 

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
	
	

	ordered_shreds = []
	ordered_shreds.append(shreds.pop())
	#while len(shreds) > 0:
	for i in xrange(10):
		print "insert i-th=%i shred" % i
		(i_left, min_left) = ordered_shreds[0].match_left(shreds)
		print "Min LEFT :",
		print  (min_left, i_left) 
		(i_right, min_right) = ordered_shreds[-1].match_right(shreds)
		print "Min RIGHT :",
		print (min_right, i_right)
		
		
		if min_left < min_right :
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
			


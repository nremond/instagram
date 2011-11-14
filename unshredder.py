#!/usr/bin/env python

from PIL import Image
import sys

from math import sqrt,log

#Configuration
threshold = 0.001
window_size = 7

# Do not change from here
surround = (window_size - 1) / 2
f_window = float(surround*2 + 1)


def calculate_difference(v1, v2):
	differences = 0
	for i in xrange(surround, len(v1)-surround, surround):	
		sum_differences = 0.0
		for channel in [0, 1, 2]:
			chan1 = sum(map(lambda x: x[channel], v1[i-surround:i+surround])) / f_window
			chan2 = sum(map(lambda x: x[channel], v2[i-surround:i+surround])) / f_window
			chan1 /= 255.0
			chan2 /= 255.0
			
			diff = (log(chan1 + 1.0, 2) - log(chan2 + 1.0, 2))**2
			sum_differences += diff
	
		if sum_differences > threshold:
			differences += 1
	return differences

	
class Shred(object):
	def __init__(self, image):
		self.image = image
		
		data = image.getdata() # This gets pixel data
		width, height = image.size
		self.left_vector = [data[y * width] for y in range(0, height)]
		self.right_vector = [data[y * width + (width-1)] for y in range(0, height)]		

	def _match(self,vref,vectors):
		distances = [calculate_difference(vref, v) for v in vectors]
		return min(enumerate(distances), key=lambda (i, v) : v)

	def match_left(self, shreds):
		return self._match(self.left_vector, [s.right_vector for s in shreds])
	
	def match_right(self, shreds):
		return self._match(self.right_vector, [s.left_vector for s in shreds])
	 

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
	while len(shreds) > 0:
		(i_left, min_left) = ordered_shreds[0].match_left(shreds)
		(i_right, min_right) = ordered_shreds[-1].match_right(shreds)
			
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
			


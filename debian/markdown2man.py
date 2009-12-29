#!/usr/bin/env python
# -*- coding: utf-8 -*-

#License
#=======
#markdown2man is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License as published by the Free
#Software Foundation, either version 2 of the License, or (at your option) any
#later version.

#markdown2man is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with persy; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

try:
	import sys
except ImportError as e:
	print "You do not have all the dependencies:"
	print str(e)
	sys.exit(1)
except Exception as e:
	print "An error occured when initialising one of the dependencies!"
	print str(e)
	sys.exit(1)

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009 Dennis Schwertel"


def main(argv):
	args = argv[1:]

	#cli options
	from optparse import OptionParser
	parser = OptionParser(usage = "use --help to get more information")
	parser.add_option("--infilename", dest="infilename", default="", help="filename of the markdown file")
	parser.add_option("--outfilename", dest="outfilename", default="", help="filename of the manpage file")
	parser.add_option("--modifydate", dest="date", default="", help="sets the modification timestamp. default is the current date")
	
	(options, args) = parser.parse_args(args)

	if not options.infilename:
		print "infilename missing"
		sys.exit(1)
	elif not options.outfilename:
		print "outfilename missing"
		sys.exit(1)
	#if date not set, set the date to right now	
	elif not options.date:
		from time import strftime
		options.date = strftime("%b %d, %Y")

	
	infile  = file(options.infilename)
	outfile = file(options.outfilename, "w")
	
	(first, last) = options.outfilename.split("/")[-1].split(".")
	
	outfile.write(".TH %s %s \"%s\"\n"%(first.upper(), last, options.date))
	

	prevline = ""
	insup = False
	for line in infile.readlines():
		#close opened RS with an RE before an new heading
		if (line.startswith("===") or line.startswith("---")) and insup:
			outfile.write(".RE\n")
			insup = False	
		#first heading
		if line.startswith("==="):
			prevline = ".SH " + prevline
			continue
		#second heading is done with an RS
		if line.startswith("---"):
			line = ".RS\n"
			insup = True

		#create formating for bold words
		bolds = line.split("__")
		if len(bolds) > 1:
			newline = ''
			i = 0
			while i < len(bolds):
				if bolds[i][0] == " ":
					newline += bolds[i][1:]
				else:
					newline += bolds[i]
				if (i + 1) < len(bolds):
					newline += "\n.B " + bolds[i+1]+"\n"
				i += 2
			line = newline
		
		#print the last line in cache
		outfile.write(prevline)
		prevline = line



if __name__ == '__main__':
	try:
		main(sys.argv)
	except Exception as e:
		print 'Unexpected error: ' + str(e)
		raise

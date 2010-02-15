# -*- coding: utf-8 -*-
# debian changelog beautifier
# parses the changelog and creates reStructuredText output for inclusion. 

import os

# here you can modify the output for each changelog entry to your needs. 
entry = '''
%(head)s - %(date)s
________________________________________________________________________________

%(changes)s
'''

def convert(infile, outfile):
	"""parses a debian changelog and converts it to reStructredText 

	Args:
	   infile (str): path to the debian changelog
	   outfile (str): path to the target output file

	Raises:
	   IOError
	"""
	if not os.path.exists(infile):
		raise IOError('infile does not exist')

	#read the changelog and prepare the temp file
	f = file(infile).read()
	if not os.path.exists(os.path.dirname(outfile)):
		os.mkdir(os.path.dirname(outfile))
	out = file(outfile, 'w')


	data = {}
	data['head'] = ''
	data['changes'] = ''
	data['date'] = ''


	for line in f.splitlines():
		if line.startswith('  * '): # get the changes
			data['changes'] += (' *   ' + line[4:].strip()+ "\n")
		elif line.startswith(' -- '): # end of a release block
			data['date'] = line[line.find('>')+1:-20].strip()
			out.write(entry % data)
			data['changes'] = ''
		else:
			if line.startswith('persy'):
				data['head'] =line[line.find('(')+1:line.find(')')].strip()

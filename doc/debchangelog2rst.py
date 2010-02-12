# -*- coding: utf-8 -*-
# debian changelog beautifier
# parses the changelog and creates reStructuredText output for inclusion. 

import os

def convert(infile, outfile):
	"""
	"""
	if not os.path.exists(infile):
		print "infile does not exist, aborting"
		return False

	#read the changelog and prepare the temp file
	f = file(infile).read()
	if not os.path.exists('_tmp'):
		os.mkdir('_tmp')
	out = file(outfile, 'w')


	data = {}
	data['head'] = ''
	data['changes'] = ''
	data['date'] = ''

	entry = '''
%(head)s - %(date)s
________________________________________________________________________________

%(changes)s
'''

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


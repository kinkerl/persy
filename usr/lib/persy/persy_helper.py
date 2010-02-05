#!/usr/bin/env python
# -*- coding: utf-8 -*-

#License
#=======
#persy is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License as published by the Free
#Software Foundation, either version 2 of the License, or (at your option) any
#later version.

#persy is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with persy; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


try:
	import gettext
	#localizations
	LOCALEDIR='/usr/lib/persy/locale'
	#init the localisation
	gettext.install("messages", LOCALEDIR)
except Exception as e:
	print "I have problems initializing the translations (gettext). Will use plain english instead"
	print str(e)

	#check if the _ function is initialized, if not, do a fallback!
	if not _:
		def _(msg):
			"""fallback-function if the original function did not initialize propperly"""
			return msg

try:
	import os
	import sys
	import subprocess2
except ImportError as e:
	print _("You do not have all the dependencies:")
	print str(e)
	sys.exit(1)
except Exception as e:
	print _("An error occured when initialising one of the dependencies!")
	print str(e)
	sys.exit(1)

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009, 2010 Dennis Schwertel"



class _PersyHelper():
	'''Functions that might be helpful in some places
	Uses singleton pattern (see bottom)'''

	def __init__(self):
		#aptCache is global for version retrieving
		#this is set with the first call of getSoftwareVersion()
		#self.aptCache = None
		pass

	def which(self, program):
		'''take from http://stackoverflow.com/questions/377017'''
		def is_exe(fpath):
			return os.path.exists(fpath) and os.access(fpath, os.X_OK)
		fpath, fname = os.path.split(program)
		if fpath:
			if is_exe(program):
				return program
		else:
			for path in os.environ["PATH"].split(os.pathsep):
				exe_file = os.path.join(path, program)
				if is_exe(exe_file):
					return exe_file
		return None

	def striplist(self, l):
		'''helper function to strip lists'''
		return ([x.strip() for x in l])

	def getSoftwareVersion(self, name):
		"""returns the version of a installed software as a String. Returns None if not installed"""
		version = None
		
		if self.which('dpkg'): #on a debian system
			callcmd = []
			callcmd.append(self.which('dpkg'))
			callcmd.append('-l')
			callcmd.append(name)
			p = subprocess2.Subprocess2(callcmd, stdout=subprocess2.PIPE, close_fds=True,)
			lines = p.getOut()
			for line in lines.splitlines():
				if line.startswith('ii'):
					version = line.split()[2]
		
		#if version not found in dpkg, maybe rpm is installed
		if not version and self.which('rpm'): #rpm system
			callcmd = []
			callcmd.append(self.which('rpm'))
			callcmd.append('--info')
			callcmd.append('-q')
			callcmd.append(name)
			p = subprocess2.Subprocess2(callcmd, stdout=subprocess2.PIPE, close_fds=True,)
			lines = p.getOut()
			for line in lines.splitlines():
				if line.startswith('Version'):
					version = line.split()[2]
		return version



#singleton hack
_singleton = _PersyHelper()
def PersyHelper(): return _singleton


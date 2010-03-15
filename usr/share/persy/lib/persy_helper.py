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
	LOCALEDIR='/usr/share/persy/locale'
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

#from __future__ import with_statement

class autorun:
	"""
	i am doing the autostart

	#autorun.add("myapp", os.path.abspath(__file__))

	base on http://29a.ch/2009/3/17/autostart-autorun-with-python
	"""
	if sys.platform == 'win32':
		import _winreg
		def __init__(self):
			self._registry = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)

		def get_runonce(self):
			return _winreg.OpenKey(self._registry,r"Software\Microsoft\Windows\CurrentVersion\Run", 0,_winreg.KEY_ALL_ACCESS)

		def add(self, name, application):
			"""add a new autostart entry"""
			key = self.get_runonce()
			_winreg.SetValueEx(key, name, 0, _winreg.REG_SZ, application)
			_winreg.CloseKey(key)

		def exists(self, name):
			"""check if an autostart entry exists"""
			key = self.get_runonce()
			exists = True
			try:
				_winreg.QueryValueEx(key, name)
			except WindowsError:
				exists = False
			_winreg.CloseKey(key)
			return exists

		def remove(self, name):
			"""delete an autostart entry"""
			key = self.get_runonce()
			_winreg.DeleteValue(key, name)
			_winreg.CloseKey(key)
	else:
		def __init__(self):
			self._xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "~/.config")
			self._xdg_user_autostart = os.path.join(os.path.expanduser(self._xdg_config_home),"autostart")

		def getfilename(self, name):
			"""get the filename of an autostart (.desktop) file"""
			return os.path.join(self._xdg_user_autostart, name + ".desktop")

		def add(self, name, application):
			"""add a new autostart entry"""
			desktop_entry = "[Desktop Entry]\n"\
				"Name=%s\n"\
				"Exec=%s\n"\
				"Type=Application\n"\
				"Terminal=false\n" % (name, application)
			with open(self.getfilename(name), "w") as f:
				f.write(desktop_entry)

		def exists(self, name):
			"""check if an autostart entry exists"""
			return os.path.exists(self.getfilename(name))

		def remove(self, name):
			"""delete an autostart entry"""
			os.unlink(self.getfilename(name))
	def test(self):
		assert not self.exists("test_xxx")
		try:
			self.add("test_xxx", "test")
			assert self.exists("test_xxx")
		finally:
			self.remove("test_xxx")
		assert not self.exists("test_xxx")

class _PersyHelper():
	"""
	Functions that might be helpful in some places.
	Singleton
	"""

	def __init__(self):
		#aptCache is global for version retrieving
		#this is set with the first call of getSoftwareVersion()
		#self.aptCache = None
		pass

	def which(self, program):
		"""
		this function is like the unix command which
		take from http://stackoverflow.com/questions/377017
		"""
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
		"""
		helper function to strip lists
		"""
		return ([x.strip() for x in l])

	def getSoftwareVersion(self, name):
		"""
		returns the version of a installed software as a String. Returns None if not installed
		"""
		version = None
		if name.lower() == 'persy':
			filename = '/usr/share/persy/assets/VERSION'
			if os.path.exists(filename):
				try:
					version = file(filename).read().strip()
				except:
					pass
		
		if not version and self.which('dpkg'): #on a debian system
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


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


__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009, 2010 Dennis Schwertel"


class VCS():
	'''Version Controll System Backend in Persy. http://norvig.com/python-iaq.html'''

	def gc(self, stdin=None, stdout=None, stderr=None, params = []): 
		'''garbage collection. clean up'''
		abstract()
		
	def init(self, bare=False, stdin=None, stdout=None, stderr=None, params = []): 
		'''initialize an empty repository'''
		abstract()
		
	def config(self,key, value, makeglobal=False, stdin=None, stdout=None, stderr=None):
		'''sets a configuration'''
		abstract()
		
	def commit(self, message, stdin=None, stdout=None, stderr=None, params = []):
		'''send commits'''
		abstract()
		
	def add(self, files, stdin=None, stdout=None, stderr=None, params = []):
		'''accepts a single file as a str or a list of files as str or file'''
		abstract()
		
	def push(self, target='', branch='', stdin=None, stdout=None, stderr=None, params = []):
		'''pushes to a repository'''
		abstract()
		
	def pull(self, target='', branch='', stdin=None, stdout=None, stderr=None, params = []):
		'''pulls from a repository'''
		abstract()
		
	def remoteAdd(self, nickname, url, stdin=None, stdout=None, stderr=None, params = []):
		'''adds a remote repository'''
		abstract()
		
	def status(self, stdin=None, stdout=None, stderr=None, params = []):
		'''prints the status messages from git'''
		abstract()
		
	def log(self, stdin=None, stdout=None, stderr=None, params = []):
		'''prints the log messages from git'''
		abstract()
		
	def command(self, cmd, stdin=None, stdout=None, stderr=None, params = []):
		'''executes a command '''
		abstract()
		
def abstract():
	import inspect
	caller = inspect.getouterframes(inspect.currentframe())[1][3]
	raise NotImplementedError(caller + ' must be implemented in subclass')


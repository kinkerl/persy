#!/usr/bin/env python

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

import os
import subprocess

GIT = '/usr/bin/git'

class PersyGit():

	def __getEnv__(self):
		ret = {}
		#ret['PWD'] = self.repositorydir
		ret['GIT_DIR'] = os.path.join(self.repositorydir, self.GIT_DIR)
		ret['GIT_WORK_TREE'] = os.path.join(self.repositorydir, self.GIT_WORK_TREE)
		return ret

	def __init__(self, repositorydir, GIT_DIR='.git', GIT_WORK_TREE='.'):
		'''repositorydir = the root git directory
GIT_DIR = the git index folder, relative to the repositorydir (default = .git)
GIT_WORK_TREE = the git repostitory, relative to the repositorydir (default = None=
'''
		self.repositorydir = repositorydir
		self.GIT_DIR = GIT_DIR
		self.GIT_WORK_TREE = GIT_WORK_TREE

	def gc(self, *params):
		'''garbage collector'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('gc')
		for param in params:
			callcmd.append(param)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("gc: "+rc)

	def init(self, bare=False, *params):
		'''initialize an empty repository'''
		callcmd = []
		callcmd.append(GIT)
		if bare:
			callcmd.append('--bare')
		callcmd.append('init')
		for param in params:
			callcmd.append(param)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("init: "+rc)

	def config(self,key, value, makeglobal=False):
		'''sets the configuration in git'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('config')
		if makeglobal:
			callcmd.append('--global')
		callcmd.append(key)
		callcmd.append(value)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("config: "+rc)

	def commit(self, message, *params):
		'''send commits'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('commit')
		for param in params:
			callcmd.append(param)
		callcmd.append('-m')
		callcmd.append(message)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("commit: "+rc)

	def add(self, files, *params):
		'''accepts a single file as a str or a list of files as str or file'''
		if type(files) is str:
			files = [files]
		for f in files:
			callcmd = []
			callcmd.append(GIT)
			callcmd.append('add')
			callcmd.append(f)
			for param in params:
				callcmd.append(param)
			rc = subprocess.Popen(callcmd, env=self.__getEnv__())
			if not rc  == 0:
				raise Exception("add: "+rc)

	def push(self, target='', branch='', *params):
		'''pushes to a repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('push')
		callcmd.append(target)
		callcmd.append(branch)
		for param in params:
			callcmd.append(param)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("push: "+rc)

	def pull(self, target='', branch='', *params):
		'''pulls from a repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('pull')
		callcmd.append(target)
		callcmd.append(branch)
		for param in params:
			callcmd.append(param)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("pull: "+rc)

	def remoteAdd(self, nickname, url, *params):
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('remote')
		callcmd.append('add')
		callcmd.append(nickname)
		callcmd.append(url)
		for param in params:
			callcmd.append(param)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("remoteAdd: "+rc)

	def status(self, *params):
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('status')
		for param in params:
			callcmd.append(param)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("status: "+rc)

	def log(self, *params):
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('log')
		for param in params:
			callcmd.append(param)
		rc = subprocess.Popen(callcmd, env=self.__getEnv__())
		if not rc  == 0:
			raise Exception("log: "+rc)

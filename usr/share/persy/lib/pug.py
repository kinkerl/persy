#!/usr/bin/env python
# -*- coding: utf-8 -*-

#License
#=======
#this is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License as published by the Free
#Software Foundation, either version 2 of the License, or (at your option) any
#later version.

#this software is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this software; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
try:
	import sys
	import os
	import subprocess2
except ImportError as e:
	print "You do not have all the dependencies:"
	print str(e)
	sys.exit(1)
	
except Exception as e:
	print "An error occured when initialising one of the dependencies!"
	print str(e)
	sys.exit(1)

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009, 2010 Dennis Schwertel"

GIT = '/usr/bin/git'

class PuG():
	"""
	persy`s uncomplicated Git.
	can execute pushs, pulls, adds, commits and so on. 
	"""

	def __init__(self, cwd='.', GIT_WORK_TREE=None, GIT_DIR=None, stdin=None, stderr=None, stdout=None):
		'''
GIT_DIR = the git index folder, relative to the repositorydir (default = .git)
GIT_WORK_TREE = the root git repostitory
'''
		self.GIT_DIR = GIT_DIR
		self.GIT_WORK_TREE = GIT_WORK_TREE
		self.stdin=stdin
		self.stderr=stderr
		self.stdout=stdout
		self.cwd = cwd
		self.lastoutput = ''

	def __getEnv(self):
		'''Gets all the default environment variables and add some new'''
		ret = os.environ
		if self.GIT_DIR:
			ret['GIT_DIR'] = self.GIT_DIR
		if self.GIT_WORK_TREE:
			ret['GIT_WORK_TREE'] = self.GIT_WORK_TREE
		return ret

	def execute(self, callcmd, stdin=None, stdout=None, stderr=None):
		'''executes any command with pug. uses the persy environment variables. returns the returncode of the process. if you want to get the output with getlastoutput, stdout must be subprocess.PIPE'''
		if not stdin:
			stdin = self.stdin
		if not stdout:
			stdout = self.stdout
		if not stderr:
			stderr = self.stderr
		p = subprocess2.Subprocess2(callcmd, stdout=stdout, stdin=stdin, stderr=stderr, close_fds=True, env=self.__getEnv(), cwd=self.cwd )# ,timeout = 10)
		if stdout == subprocess2.PIPE:
			self.lastoutput = p.getOut()
		return p.process.returncode

	def gc(self, stdin=None, stdout=None, stderr=None, params = []):
		'''garbage collector'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('gc')
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		if not rc  == 0:
			raise Exception("gc: %i "%rc)

	def init(self, bare=False, stdin=None, stdout=None, stderr=None, params = []):
		'''initialize an empty repository'''
		callcmd = []
		callcmd.append(GIT)
		if bare:
			callcmd.append('--bare')
		callcmd.append('init')
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		#0 = all ok, 128 = reinitialized, all ok
		if not (rc  == 0 or rc == 128):
			raise Exception("init: %i "%rc)

	def config(self,key, value, makeglobal=False, stdin=None, stdout=None, stderr=None):
		'''sets the configuration in git'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('config')
		if makeglobal:
			callcmd.append('--global')
		callcmd.append(key)
		callcmd.append(value)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		if not rc  == 0:
			raise Exception("config: %i"%rc)

	def commit(self, message, stdin=None, stdout=None, stderr=None, params = []):
		'''send commits'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('commit')
		for param in params:
			callcmd.append(param)
		callcmd.append('-m')
		callcmd.append(message)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		#dont know! rc == 1 = nothing new added to commit!
		if not (rc  == 0 or rc == 1 or rc == 128):
			raise Exception("commit: %i"%rc)

	def command(self, cmd, stdin=None, stdout=None, stderr=None, params = []):
		'''executes any command, but with environment variables set. mainly used the start gitk in a nice way'''
		callcmd = []
		callcmd.append(cmd)
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		if not rc  == 0:
			raise Exception("command %s: %i"%(cmd,rc))


	def add(self, files, stdin=None, stdout=None, stderr=None, params = []):
		'''accepts a single file as a str or a list of files as str or file'''
		if type(files) is str:
			files = [files]
		for f in files:
			callcmd = []
			callcmd.append(GIT)
			callcmd.append('add')
			callcmd.append('-A') # removes deleted files!
			callcmd.append(f)
			for param in params:
				callcmd.append(param)
			rc = self.execute(callcmd, stdin, stdout, stderr)
			if not rc  == 0:
				raise Exception("add: %i "%rc)

	def push(self, target='', branch='', stdin=None, stdout=None, stderr=None, params = []):
		'''pushes to a repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('push')
		callcmd.append(target)
		callcmd.append(branch+":refs/heads/"+branch)
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		#no errors or nothing to push (128)
		if rc == 1:
			raise Exception("Can not push to server. Maybe the server or the network is not available(%i)"%rc)		
		if not (rc == 0 or rc == 128):
			raise Exception("push: %i"%rc)

	def pull(self, target='', branch='', stdin=None, stdout=None, stderr=None, params = []):
		'''pulls from a repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('pull')
		callcmd.append(target)
		callcmd.append(branch)
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		#no errors or nothing to pull (128)
		if rc == 1:
			raise Exception("Can not pull from server. Maybe the server or the network is not available(%i)"%rc)		
		if not (rc == 0 or rc == 128):
			raise Exception("pull: %i"%rc)

	def svn_pull(self, stdin=None, stdout=None, stderr=None, params = []):
		'''pulls from a svn repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('svn')
		callcmd.append('rebase')
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		if rc == 1:
			raise Exception("Can not pull from server. Maybe the server or the network is not available(%i)"%rc)		

		if not (rc == 0):
			raise Exception("git-svn: %i"%rc)

	def svn_push(self, stdin=None, stdout=None, stderr=None, params = []):
		'''pushes commits to a svn repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('svn')
		callcmd.append('dcommit')
		rc = self.execute(callcmd, stdin, stdout, stderr)
		#dont know! rc == 1 = nothing new added to commit!
		if not (rc  == 0):
			raise Exception("svn-commit: %i"%rc)

	def svn_init(self, url, stdin=None, stdout=None, stderr=None, params = []):
		'''initialize an empty repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('svn')
		callcmd.append('init')
		callcmd.append(url)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		#0 = all ok, 128 = reinitialized, all ok
		if not (rc  == 0):
			raise Exception("init: %i "%rc)

	def remoteAdd(self, nickname, url, stdin=None, stdout=None, stderr=None, params = []):
		'''adds a remote repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('remote')
		callcmd.append('add')
		callcmd.append(nickname)
		callcmd.append(url)
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		if not rc  == 0:
			raise Exception("remoteAdd: %i"%rc)

	def status(self, stdin=None, stdout=None, stderr=None, params = []):
		'''prints the status messages from git'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('status')
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		#status doesnt return 0 if everything is ok so we skip this test
		#if not rc  == 0:
		#	raise Exception("status: %i"%rc)

	def log(self, stdin=None, stdout=None, stderr=None, params = []):
		'''prints the log messages from git'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('log')
		for param in params:
			callcmd.append(param)
		rc = self.execute(callcmd, stdin, stdout, stderr)
		if not rc  == 0:
			raise Exception("log: %i"%rc)


	def get_submodules(self, stdin=None, stdout=None, stderr=None, include_dir = None):
		'''returns an array of all the submodules'''
		submodules = []
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('submodule')
		callcmd.append('foreach')
		callcmd.append('cd .')
		rc = self.execute(callcmd, subprocess2.PIPE, subprocess2.PIPE, stderr)
		if not rc  == 0:
			raise Exception("log: %i"%rc)
		stdoutdata = self.getLastOutput()
		for entry in stdoutdata.split("\n"):
			possible_module = entry[entry.find("'")+1:entry.rfind("'")]
			if possible_module and os.path.exists(possible_module):
				if include_dir:
					for inc in include_dir:
						if os.path.abspath(possible_module).startswith(os.path.abspath(inc)):
							submodules.append(possible_module)
		return submodules

	def getLastOutput(self):
		'''returns the output of the last executed command if stdout was set to subprocess2.PIPE'''
		return self.lastoutput


if __name__== '__main__':

	git = PuG(stdout=sys.stdout)
	print "executing git status"
	git.status()

	print "executing git status piped!"
	git.status(stdout=subprocess2.PIPE)
	print git.getLastOutput()



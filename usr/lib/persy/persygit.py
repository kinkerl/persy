#!/usr/bin/env python

import os

GIT = '/usr/bin/git'

Class PersyGit():
	self.workdirectory = ""

	def __init__(self, workdirectory):
		self.workdirectory = workdirectory

	def init(self, bare=False):
		if bare:
			cbare = '--bare'
		else:
			cbare = ''
		os.popen("%s %s init"%(GIT, cbare))

	def config(self,key, value, makeglobal=False)
		cmd = "%s config "%GIT
		if makeglobal:
			cmd += '--global'
		cmd += " %s %s"%(key,value)
		os.popen(cmd)

	def commit(self, message):
		'''send commits'''
		os.popen("%s commit -am \"Backup by me\""%GIT)

	def add(self, files):
		'''accepts a single file as a str or a list of files as str or file'''
		if type(files) is str:
			files = [files]
		for f in files:
			os.popen("%s add %s"%(GIT, f))

	def push(self, target='', branch=''):
		os.popen("%s push %s %s"%(GIT, target, branch))

	def pull(self, target='', branch=''):
		os.popen("%s pull %s %s"%(GIT,target, branch))

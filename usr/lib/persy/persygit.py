#!/usr/bin/env python

import os
import subprocess

GIT = '/usr/bin/git'

class PersyGit():

	def __precmd__():
		return "GIT_DIR=%s; GIT_WORKING_TREE=%s;"%(os.path.join(self.repositorydir, self.GIT_DIR),os.path.join(self.repositorydir, self.GIT_WORKING_TREE))

	def __init__(self, repositorydir):
		self.repositorydir = repositorydir
		self.GIT_DIR = '.git'
		self.GIT_WORKING_TREE ='.'

	def init(self, bare=False):
		'''initialize an empty repository'''
		callcmd = []
		callcmd.append(GIT)
		if bare:
			callcmd.append('--bare')
		callcmd.append('init')
		subprocess.check_call(callcmd)

	def config(self,key, value, makeglobal=False):
		'''sets the configuration in git'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('config')
		if makeglobal:
			callcmd.append('--global')
		callcmd.append(key)
		callcmd.append(value)
		subprocess.check_call(callcmd)

	def commit(self, message):
		'''send commits'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('commit')
		callcmd.append('-am')
		callcmd.append(message)
		subprocess.check_call(callcmd)

	def add(self, files):
		'''accepts a single file as a str or a list of files as str or file'''
		if type(files) is str:
			files = [files]
		for f in files:
			callcmd = []
			callcmd.append(GIT)
			callcmd.append('add')
			callcmd.append(f)
			subprocess.check_call(callcmd)

	def push(self, target='', branch=''):
		'''pushes to a repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('push')
		callcmd.append(target)
		callcmd.append(branch)
		subprocess.check_call(callcmd)

	def pull(self, target='', branch=''):
		'''pulls from a repository'''
		callcmd = []
		callcmd.append(GIT)
		callcmd.append('pull')
		callcmd.append(target)
		callcmd.append(branch)
		subprocess.check_call(callcmd)

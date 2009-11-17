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
	import sys
	from pyinotify import WatchManager, Notifier, ThreadedNotifier, ProcessEvent, EventsCodes
	from subprocess import Popen
	from threading import Thread
	from persy_config import PersyConfig
	from persy_helper import PersyHelper
	from persy_syncer import TheSyncer, FileChangeHandler
	import os
	import paramiko
	import pug
	import subprocess
except ImportError as e:
	print _("You do not have all the dependencies:")
	print str(e)
	sys.exit(1)
except Exception as e:
	print _("An error occured when initialising one of the dependencies!")
	print str(e)
	sys.exit(1)

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009 Dennis Schwertel"


class _Core():
	def init(self, config, log):
		self.config = config
		self.log = log
		self.worker = None
		self.notifier = None

		#initialzing the git binding
		#===========================
		#if persy is interrupted while git was running, a git.lockfile may be present. we have to remove it!
		if os.path.exists(self.config.getAttribute('GIT_LOCKFILE')):
			try: 
				os.remove(self.config.getAttribute('GIT_LOCKFILE'))
			except Exception as e:
				log.warn(str(e))
			else:
				log.warn(_("removed git lock file"))

		#init pug
		os.popen("touch %s"%self.config.getAttribute('LOGFILE_GIT'))
		std = open(self.config.getAttribute('LOGFILE_GIT'), 'a')
		stdin = None #default stdin
		stdout = std #default stdout
		stderr = std #default stderr
		self.git = pug.PuG(self.config.getAttribute('USERHOME'), GIT_DIR=self.config.getAttribute('GIT_DIR'), stdin=stdin, stdout=stdout, stderr=stderr)


	def initLocal(self):
		'''initialises the local repository'''
		if not self.config.has_key('general') or not self.config['general'].has_key('name') or not self.config['general']['name'] :
			self.log.critical(_('username not set, cannot create git repository. use "persy --config --name=NAME" to set one'), verbose=True)
			sys.exit(-1)
		if not self.config.has_key('general') or not self.config['general'].has_key('mail') or not self.config['general']['mail']:
			self.log.critical(_('mail not set, cannot create git repository. use "persy --config --mail=MAIL" to set one'), verbose=True)
			sys.exit(-1)

		self.log.info(_("initialising local repository..."), verbose=True)
	
		try:
			self.git.init()
			self.git.config('user.name',self.config['general']['name'])
			self.git.config('user.email',self.config['general']['mail'])
			self.gitignore()
		except Exception as e:
			self.log.critical(str(e), verbose=True)
		else:
			self.log.info(_("done"), verbose=True)



	def gitlog(self):
		'''executes the git-log command'''
		self.git.log(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

	def gitstatus(self):
		'''executes the git-status command'''
		self.git.status(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)



	def initRemote(self):
		'''initialises the remote repository'''

		self.log.info(_("initialising and adding remote repository..."), verbose=True)
		try:	
			client = paramiko.SSHClient()
			client.load_system_host_keys()
			client.connect(self.config['remote']['hostname'] )
			# the follow commands are executet on a remote host. we can not know the path to git,
			# mkdir and cd so we will not replace them with a absolute path
			stdin1, stdout1, stderr1 = client.exec_command("mkdir -m 700 %s"%self.config['remote']['path'])
			stdin2, stdout2, stderr2 = client.exec_command("cd %s && git --bare init"%self.config['remote']['path'])
			client.close()
			if stderr1:
				self.log.warn(_("error creating dir, maybe it exists already?"), verbose=True)
			elif stderr2:
				self.log.critical(_("error on remote git init"), verbose=True)
			elif not self.config['remote']['use_remote']:
				#no errors:so we are save to use the remote
				self.config['remote']['use_remote'] = True
				self.config.write()

			self.git.remoteAdd(self.config.getAttribute('SERVER_NICK'),"ssh://%s/%s"%(self.config['remote']['hostname'],self.config['remote']['path']))
		except Exception as e:
			self.log.critical(str(e), verbose=True)
		else:
			self.log.info(_("done"), verbose=True)


	def syncWithRemote(self):
		'''Syncs with a remote server'''
		#i dont use clone because of massive errors when using it
		self.initLocal()
		try:
			self.git.remoteAdd(self.config.getAttribute('SERVER_NICK'),"ssh://%s/%s"%(self.config['remote']['hostname'],self.config['remote']['path']))
			self.git.pull(self.config.getAttribute('SERVER_NICK'),self.config.getAttribute('BRANCH'))
		except Exception as e:
			self.log.critical(str(e))

		if not self.config['remote']['use_remote']:
			self.config['remote']['use_remote'] = True
			self.config.write()

	def gitignore(self):
		'''creates a file for ignoring unwatched directories so they dont appear in the status (and cant be removed exidently with "git clean")'''
		#list every file in /home/USER
		#add every file and folder (if not already done) to .gitignore if they are not part WATCHED
		current = os.listdir(self.config.getAttribute('USERHOME'))
		for f in self.config['local']['watched']:
			#if not f.startswith(USERHOME):
			if f.startswith(self.config.getAttribute('USERHOME')): #if absolute path
			#strip dir stuff, the +1 is for the file seperator
				f = f[len(self.config.getAttribute('USERHOME'))+1:]
			elif f.startswith('~/'):
				f = f[2:] #strip the ~/
			elif f.startswith('./'):
				f = f[2:] #strip the ./
			elif f.startswith('/'):
				#continue #savetycheck
				#i assume if it still starts with /, its outside of /home
				continue

			if os.sep in f:
				f = f[:f.index(os.sep)]
			if f in current:
				current.remove(f)

			if self.config['local']['maxfilesize']:
				callcmd = []
				callcmd.append('find')
				callcmd.append(os.path.join(self.config.getAttribute('USERHOME'),f))
				callcmd.append('-type')
				callcmd.append('f')
				callcmd.append('-size')
				callcmd.append("+" + str(self.config['local']['maxfilesize']) + "k")
				(stdoutdata, stderrdata) = subprocess.Popen(callcmd, stdout=subprocess.PIPE).communicate()
				for entry in stdoutdata.split("\n"):
					current.append(entry)

		for entry in self.config['local']['exclude']:
			current.append(entry)

		with open(os.path.join(self.config.getAttribute('PERSY_DIR'),self.config.getAttribute('GITIGNOREFILE')), "w+") as f:
			for c in current:
				f.write(c+"\n")


	def optimize(self):
		'''executes git-gc'''
		self.log.info('starting optimization', verbose=True)
		class Starter(Thread):
			def __init__(self,git, log):
				Thread.__init__(self)
				self.git = git
				self.log = log
			def run(self):
				try:
					self.log.debug('git gc')
					self.git.gc()
				except Exception as e:
					self.log.warn(str(e), verbose=True)

		try:
			Starter(self.git, self.log).start()
		except Exception as e:
			self.log.warn(str(e), verbose=True)



	#just ignore the widget if started from cli
	def browse(self, wiget=None):
		'''starts the default git browser'''
		class Starter(Thread):
			def __init__(self,git, config):
				Thread.__init__(self)
				self.git = git
				self.config = config
			def run(self):
				self.git.command(self.config['general']['prefgitbrowser'], stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)
		Starter(self.git, self.config).start()


	def persy_start(self):
		''' Starts Persy'''
		self.log.info("start working")

		FLAGS=EventsCodes.ALL_FLAGS
		mask = FLAGS['IN_MODIFY'] | FLAGS['IN_DELETE_SELF']|FLAGS['IN_DELETE'] | FLAGS['IN_CREATE'] | FLAGS['IN_CLOSE_WRITE'] | FLAGS['IN_MOVE_SELF'] | FLAGS['IN_MOVED_TO'] | FLAGS['IN_MOVED_FROM'] # watched events

		wm = WatchManager()
		#addin the watched directories
		for watch in self.config['local']['watched']:
			wdd = wm.add_watch("%s"%(watch), mask, rec=True, auto_add=True)

		self.log.debug("init the syncer")
		self.worker = TheSyncer(self, self.config, self.log, self.config['remote']['sleep'], self.config['local']['sleep'])
		self.log.debug("init the filesystem notifier")
		self.notifier = ThreadedNotifier(wm, FileChangeHandler(self.log, self.worker.newEvent))
		self.log.resetError()
		self.log.debug("starting syncer")
		self.worker.start()
		self.notifier.start()
		self.log.setStart()
		#if self.statusIcon:
		#	statusIcon.set_from_file(config.getAttribute('ICON_OK'))#from_stock(gtk.STOCK_HOME)

	def git_add(self, item):
		self.git.add(item)
		
	def git_commit(self, item):
		self.git.commit(item)

	def git_pull(self, item, item2):
		self.git.pull(item, item2)

	def git_push(self, item, item2):
		self.git.push(item,item2)

	def setonetimesync(self):
		if self.worker:
			try:
				self.worker.setonetimesync()
			except RuntimeError:
				pass


	def persy_stop(self):
		'''Stops Persy'''

		self.log.info("stop working")
		if self.worker:
			try:
				self.worker.stop()
				self.worker.join()
			except RuntimeError:
				pass
		if self.notifier:
			try:
				self.notifier.stop()
			except RuntimeError:
				pass
			except OSError:
				pass
			except KeyError:
				pass
		self.log.setStop()
		#if statusIcon:
		#	statusIcon.set_from_file(config.getAttribute('ICON_IDLE'))#from_stock(gtk.STOCK_HOME)

#singleton hack
_singleton = _Core()
def Core(): return _singleton


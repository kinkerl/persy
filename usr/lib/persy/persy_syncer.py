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
	import os
	import time
	import logging , logging.handlers
	import time, signal, operator
	import paramiko
	import pug
	import pynotify
	import subprocess
	import gtk
	import pygtk
	pygtk.require("2.0")
except ImportError as e:
	print _("You do not have all the dependencies:")
	print str(e)
	sys.exit(1)
except Exception as e:
	print _("An error occured when initialising one of the dependencies!")
	print str(e)
	sys.exit(1)

lastevent = 0

class FileChangeHandler(ProcessEvent):
	'''Callback for the pyinotify library. 
Accepts events from the library if a file changes and sets the lastevent time and sets the untracked_changes flag to True'''

	def __init__(self, log):
		self.log = log

	def process_IN_MODIFY(self, event):
		self.check(event, "IN_MODIFY")

	def process_IN_DELETE_SELF(self, event):
		self.check(event, "IN_DELETE_SELF")

	def process_IN_DELETE(self, event): 
		self.check(event, "IN_DELETE")

	def process_IN_CREATE(self, event):
		self.check(event, "IN_CREATE")

	def process_IN_CLOSE_WRITE(self, event):
		self.check(event, "IN_CLOSE_WRITE")

	def process_IN_MOVE_SELF(self, event):
		self.check(event, "IN_MOVE_SELF")

	def process_IN_MOVED_TO(self, event):
		self.check(event, "IN_MOVED_TO")

	def process_IN_MOVED_FROM(self, event):
		self.check(event, "IN_MOVED_FROM")

	def check(self, event, typ="undefined"):
		global lastevent
		try:
			self.log.debug("%s: %s"% (typ, event.path))
		except Exception as e:
			self.log.warn(_("error with %s event. maybe problem with path?")%typ)
			self.log.warn(str(e))
		
		lastevent = time.time()
		self.log.untracked_changes(True)





class TheSyncer(Thread):
	'''The syncing logic.
executing the local commits, the remote pulls/pushs and the updating of the ignore file after self.ignore_time minutes.
'''

	def __init__(self, core, config, log, sleep_remote, sleep_local):
		Thread.__init__(self)
		self.core = core
		self.config = config
		self.sleep_remote = sleep_remote
		self.sleep_local = sleep_local
		self.ignore_time = 60 #one hour
		self.lastcommit = -1
		self.lastsync = -1
		self.lastignore = -1
		self.running = True
		self.onetimesync = False #if set will sync one time!
		self.errorlocalcounter = 0
		self.errorremotecounter = 0
		self.log = log

		
	def setonetimesync(self):
		self.onetimesync = True

	def generateCommitMessage(self):
		'''generates a nice commit message'''
		commitDesc = 'Backup by me'
		if self.config['general']['fortune']:
			try:
				callcmd = []
				callcmd.append(FORTUNE)
				callcmd.append('-n')
				callcmd.append('80')
				callcmd.append('-s')
				(stdoutdata, stderrdata) = subprocess.Popen(callcmd, stdout=subprocess.PIPE).communicate()
				commitDesc = stdoutdata.strip("\n\r")
			except Exception as e:
				pass #just silently do nothing
		return commitDesc

	def stop(self):
		self.running = False

	def run(self):
		self.running = True

		while self.running:
			time.sleep(self.sleep_local)
			self.log.debug('tick')
			global lastevent
			#only do if changed occured (dome==True) and only at least 2 seconds after the last event

			if not self.lastcommit == lastevent and time.time() - lastevent > self.sleep_local:
				self.lastcommit = lastevent
				self.log.info('local commit')
				if self.config['local']['watched']:
					self.log.debug('git ignore')
					self.lastignore = time.time()
					try:
						self.core.gitignore()
					except Exception as e:
						self.errorlocalcounter += 1
						if self.errorlocalcounter > 1:
							self.log.warn(str(e))


					self.log.debug('git add')
					try:
						self.core.git_add(self.config['local']['watched'])
					except Exception as e:
						self.errorlocalcounter += 1
						if self.errorlocalcounter > 1:
							self.log.warn(str(e))

					self.log.debug('git commit')
					try:
						self.core.git_commit(self.generateCommitMessage())
					except Exception as e:
						self.errorlocalcounter += 1
						if self.errorlocalcounter > 1:						
							self.log.critical(str(e))
					else: 
						self.errorlocalcounter = 0					
						self.log.unsynced_changes(True)

			#autopull and push updates every x secs
			if self.onetimesync or (self.config['remote']['use_remote'] and time.time() - self.lastsync > self.sleep_remote):
				self.onetimesync = False
				self.lastsync = time.time()
				self.log.info('remote sync')
				if self.config['local']['watched']:
					okcounter = 0
					self.log.debug('git pull')
					try:
						self.core.git_pull(self.config.getAttribute('SERVER_NICK'),self.config.getAttribute('BRANCH'))
					except Exception as e:
						self.errorremotecounter += 1
						if self.errorremotecounter > 2:
							self.log.critical(str(e))
					else:
						okcounter += 1

					self.log.debug('git push')
					try:
						self.core.git_push(self.config.getAttribute('SERVER_NICK'),self.config.getAttribute('BRANCH'))
					except Exception as e:
						self.errorremotecounter += 1
						if self.errorremotecounter > 2:					
							self.log.critical(str(e))
					else:
						okcounter += 1

					if okcounter >= 2:
						self.errorlocalcounter = 0	
						self.log.unsynced_changes(False)
			#start git ignore on a regular basis (ignoring unwatched files)
			if time.time() - self.lastignore >  self.ignore_time:
				self.lastignore = time.time()
				try:
					self.core.gitignore()
				except Exception as e:
					self.log.warn(str(e))

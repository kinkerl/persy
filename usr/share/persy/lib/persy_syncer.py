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
	import sys
	from pyinotify import ProcessEvent
	from threading import Thread
	import time
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
__copyright__ = "Copyright (C) 2009, 2010 Dennis Schwertel"


class FileChangeHandler(ProcessEvent):
	"""
	Callback for the pyinotify library. 
	Accepts events from the library if a file changes and sets the lastevent time and sets the untracked_changes flag to True
	"""

	def __init__(self, log, eventfunc):
		self.log = log
		self.eventfunc = eventfunc

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
		"""
		this function is executed on every file event.
		then the eventfunc is called with the information from the event.
		the eventfunc is passed to FileChangeHandler on __init__
		"""
		try:
			self.log.debug("%s: %s"% (typ, event.path))
		except Exception as e:
			self.log.warn(_("error with %s event. maybe problem with path?")%typ)
			self.log.warn(str(e))
		if event.pathname:
			self.eventfunc(time.time(), event.pathname)
		else: #backup incase the pathname does not exist
			self.eventfunc(time.time(), event.path)
		self.log.untracked_changes(True)





class TheSyncer(Thread):
	"""
	The syncing logic.
	executing the local commits, the remote pulls/pushs and the updating of the ignore file after self.ignore_time minutes.
	"""

	def __init__(self, core, config, log, sleep_remote, sleep_local):
		Thread.__init__(self)
		self.lastevent = 0
		self.core = core
		self.config = config
		self.sleep_remote = sleep_remote
		self.sleep_local = sleep_local
		self.ignore_time = 60 #one hour
		self.lastcommit = -1
		self.lastsync = -1
		self.lastignore = -1
		self.running = True
		self.onetimesync = False #if set, will sync one time!
		self.onetimecommit = False #if set, will commit one time!
		self.errorlocalcounter = 0
		self.errorremotecounter = 0
		self.log = log

		self.changedFiles  =[]

	def newEvent(self, time, filename):
		"""
		used to register a filechange event.
		this function is passed to FileChangeHandler in PersyCore when creating a new instance of the class
		"""
		self.lastevent = time
		self.changedFiles.append(filename)
		
	def setonetimesync(self):
		self.onetimesync = True

	def setonetimecommit(self):
		self.onetimecommit = True

	def generateCommitMessage(self):
		"""
		generates a nice commit message. 
		uses fortune if possible
		"""
		commitDesc = 'Backup by me'
		if self.config['general']['fortune']:
			try:
				callcmd = []
				callcmd.append(self.config.getAttribute('FORTUNE'))
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
		"""
		startes the thread and checks for file change events.
		does the pull, push and commits
		"""
		self.running = True

		while self.running:
			time.sleep(self.sleep_local)
			self.log.debug('tick')
			if self.onetimecommit or (not self.lastcommit == self.lastevent and time.time() - self.lastevent > self.sleep_local):
				self.onetimecommit = False
				self.lastcommit = self.lastevent
				self.log.info('local commit')
				if self.config['local']['watched']:
					self.log.debug('git ignore')
					self.lastignore = time.time()
					try:
						self.core.vcsignore()
					except Exception as e:
						self.log.warn(str(e))

					self.log.debug('git add')
					try:
						if self.config['general']['autoshare']:
							self.core.git_add(self.config.getAttribute('CONFIGFILE'))

						#add all files
						self.core.git_add(self.config['local']['watched'])

						#i dont know if this is still necessary
						#explicit add changed files
						processFiles = self.changedFiles
						self.changedFiles = []
						try:
							self.core.git_add(processFiles)
						except Exception as e:
							#most of the time this is only triggerted
							#if a file is changed in a git submodule. 
							#i dont know any good way to check for this
							#so ignore the direct error and write this to debug
							self.log.debug(str(e))

					except Exception as e:
						#self.errorlocalcounter += 1
						#if self.errorlocalcounter > 1:
						self.log.warn(str(e))

					self.log.debug('git commit')
					try:
						self.core.git_commit(self.generateCommitMessage())
					except Exception as e:
						#self.errorlocalcounter += 1
						#if self.errorlocalcounter > 1:
						self.core.persy_stop()
						self.log.critical(str(e))
					else: 
						self.errorlocalcounter = 0					
						self.log.unsynced_changes(True)
				else:
					self.log.debug(_('watching no directories')) 

			#autopull and push updates every x secs
			if self.onetimesync or (self.config['remote']['use_remote'] and time.time() - self.lastsync > self.sleep_remote):
				self.log.info('trying remote sync')
				if self.config['local']['watched']:
					okcounter = 0
					self.log.debug('git pull')
					try:
						if self.config['remote']['use_gitsvn']:
							self.core.git_svn_pull()
						else:
							self.core.git_pull(self.config.getAttribute('SERVER_NICK'),self.config.getAttribute('BRANCH'))					
					except Exception as e:
						self.errorremotecounter += 1
						if self.errorremotecounter > 2:
							self.core.persy_stop()
							self.log.critical(str(e))
					else:
						okcounter += 1

					self.log.debug('git push')
					try:
						if self.config['remote']['use_gitsvn']:
							self.core.git_svn_push()
						else:
							self.core.git_push(self.config.getAttribute('SERVER_NICK'),self.config.getAttribute('BRANCH'))
					except Exception as e:
						self.errorremotecounter += 1
						if self.errorremotecounter > 2:		
							self.core.persy_stop()
							self.log.critical(str(e))
					else:
						okcounter += 1

					if okcounter >= 2:
						self.log.info('done remote sync')
						self.onetimesync = False
						self.lastsync = time.time()
						self.errorlocalcounter = 0	
						self.log.unsynced_changes(False)
			#start git ignore on a regular basis (ignoring unwatched files)
			if time.time() - self.lastignore >  self.ignore_time:
				self.log.debug('git ignore')
				self.lastignore = time.time()
				try:
					self.core.vcsignore()
				except Exception as e:
					self.log.warn(str(e))

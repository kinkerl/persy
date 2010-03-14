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
	LOCALEDIR = '/usr/lib/persy/locale'
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
	from pyinotify import WatchManager, ThreadedNotifier, EventsCodes
	from threading import Thread
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
__copyright__ = "Copyright (C) 2009, 2010 Dennis Schwertel"


class _Core():
	"""
	the core functionaliy for persy
	"""

	def init(self, config, log):
		"""
		initializes the git binding
		"""
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
			except Exception as err:
				log.warn(str(err))
			else:
				log.warn(_("removed git lock file"))

		#init pug
		os.popen("touch %s"%self.config.getAttribute('LOGFILE_GIT'))
		std = open(self.config.getAttribute('LOGFILE_GIT'), 'a')
		stdin = None #default stdin
		stdout = std #default stdout
		stderr = std #default stderr
		self.vcs = pug.PuG(self.config.getAttribute('USERHOME'), GIT_DIR=self.config.getAttribute('GIT_DIR'), stdin=stdin, stdout=stdout, stderr=stderr)

	def init_local(self):
		"""
		initialises the local repository
		"""
		if not self.config.has_key('general') or not self.config['general'].has_key('name') or not self.config['general']['name'] :
			self.log.critical(_('username not set, cannot create git repository. use "persy --config --name=NAME" to set one'), verbose=True)
			sys.exit(-1)
		if not self.config.has_key('general') or not self.config['general'].has_key('mail') or not self.config['general']['mail']:
			self.log.critical(_('mail not set, cannot create git repository. use "persy --config --mail=MAIL" to set one'), verbose=True)
			sys.exit(-1)

		self.log.info(_("initialising local repository..."), verbose=True)

		try:
			self.vcs.init()
			self.vcs.config('user.name',self.config['general']['name'])
			self.vcs.config('user.email',self.config['general']['mail'])
			self.vcsignore()
		except Exception as err:
			self.log.critical(str(err), verbose=True)
		else:
			self.log.info(_("done"), verbose=True)


	def vcslog(self):
		"""
		runs the vcs(git)-log command and writs the output to stdout
		"""
		self.vcs.log(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)


	def vcsstatus(self):
		"""
		runs the vcs(git)-status command
		"""
		self.vcs.status(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)


	def initRemote(self):
		"""
		initialises the remote repository and adds it to the synchronization pack
		
		tries to connect to the remote server and creates the destination folder and initializes the remote git repository
		"""
		self.log.info(_("initialising and adding remote repository..."), verbose=True)
		try:	
			client = paramiko.SSHClient()
			client.load_system_host_keys()
			client.connect(self.config['remote']['hostname'],
							username=self.config['remote']['username'],
							port=int(self.config['remote']['port']))
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

			self.vcs.remoteAdd(self.config.getAttribute('SERVER_NICK'),"ssh://%s@%s/%s"%(self.config['remote']['username'],self.config['remote']['hostname'],self.config['remote']['path']))
		except Exception as e:
			self.log.critical(str(e), verbose=True)
		else:
			self.log.info(_("done"), verbose=True)


	def syncWithRemote(self):
		"""
		Syncs with a remote server
		
		adds a new remote repository with the information from config to the local git repository and performs a pull
		"""
		# i dont use clone because of massive errors when using it
		# the best way iś to add the remote server and pull from it
		try:
			self.vcs.remoteAdd(self.config.getAttribute('SERVER_NICK'),"ssh://%s@%s/%s"%(self.config['remote']['username'],self.config['remote']['hostname'],self.config['remote']['path']))
			self.vcs.pull(self.config.getAttribute('SERVER_NICK'),self.config.getAttribute('BRANCH'))
		except Exception as e:
			self.log.critical(str(e))

		if not self.config['remote']['use_remote']:
			self.config['remote']['use_remote'] = True
			self.config.write()


	def isInSyncWithRemote(self):
		"""
		returns true if it is already in sync
		
		"in sync" means: git remote returns an entry for an "origin" repository.
		"""
		try:
			self.vcs.command('git', params=['remote'])
		except Exception as e:
			self.log.critical(str(e))
		std = self.vcs.getLastOutput().strip("\n ")
		if std == 'origin':
			return True
		return False


	def vcsignore(self):
		"""
		creates a file for ignoring unwatched directories so they dont appear in the status (and cant be removed exidently with "git clean")
		
		list every file in /home/USER. 
		add every file and folder (if not already done) to .vcsignore if they are not part WATCHED
		"""
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

			if self.config['local']['maxfilesize'] and self.config['local']['maxfilesize'] > 0:
				#add files to the ignorelist if they are larger than maxfilesize
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
		"""
		tries to optimize the local repository.
		executes the git-gc command. 
		"""
		self.log.info('starting optimization', verbose=True)
		class Starter(Thread):
			def __init__(self,vcs, log):
				Thread.__init__(self)
				self.vcs = vcs
				self.log = log
			def run(self):
				try:
					self.log.debug('git gc')
					self.vcs.gc()
				except Exception as e:
					self.log.warn(str(e), verbose=True)

		try:
			Starter(self.vcs, self.log).start()
		except Exception as e:
			self.log.warn(str(e), verbose=True)


	def browse(self):
		"""
		starts the default git browser
		"""
		class Starter(Thread):
			def __init__(self,vcs, config):
				Thread.__init__(self)
				self.vcs = vcs
				self.config = config
			def run(self):
				self.vcs.command(self.config['general']['prefgitbrowser'], stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)
		Starter(self.vcs, self.config).start()


	def persy_stop(self):
		"""
		Stops persys working thread and the notifier.
		"""
		self.log.info("stop working")
		self.log.setStop()

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


	def persy_start(self):
		"""
		initializes the worker thread and notifier
		"""
		self.log.info("start working")
		self.log.setStart()
		FLAGS=EventsCodes.ALL_FLAGS
		mask = FLAGS['IN_MODIFY'] | FLAGS['IN_DELETE_SELF']|FLAGS['IN_DELETE'] | FLAGS['IN_CREATE'] | FLAGS['IN_CLOSE_WRITE'] | FLAGS['IN_MOVE_SELF'] | FLAGS['IN_MOVED_TO'] | FLAGS['IN_MOVED_FROM'] # watched events

		wm = WatchManager()
		#addin the watched directories
		for watch in self.config['local']['watched']:
			wdd = wm.add_watch("%s"%(watch), mask, rec=True, auto_add=True)

		#watch for changes of the configurationfile
		if self.config['general']['autoshare']:
			wdd = wm.add_watch(self.config.getAttribute('CONFIGFILE'), mask, rec=True, auto_add=True)

		self.log.debug("init the syncer")
		self.worker = TheSyncer(self, self.config, self.log, self.config['remote']['sleep'], self.config['local']['sleep'])
		self.log.debug("init the filesystem notifier")
		self.notifier = ThreadedNotifier(wm, FileChangeHandler(self.log, self.worker.newEvent))
		self.log.resetError()
		self.log.debug("starting syncer")
		self.worker.start()
		self.notifier.start()
		
		#if self.statusIcon:
		#	statusIcon.set_from_file(config.getAttribute('ICON_OK'))#from_stock(gtk.STOCK_HOME)


	def setonetimesync(self):
		"""
		if the worker is running, execute the setonetimesync function of the worker
		"""
		if self.worker:
			try:
				self.worker.setonetimesync()
			except RuntimeError:
				pass


	def isLocalInitialized(self):
		"""
		returns true if the local GIT_DIR exists
		"""
		return os.path.exists(self.config.getAttribute('GIT_DIR'))


	def git_add(self, item):
		"""
		adds an item to git
		"""
		self.vcs.add(item)

	def git_commit(self, message):
		"""
		executes a commit with "message" as the commit message
		"""
		self.vcs.commit(message)

	def git_pull(self, nickname, branch):
		"""
		executes a pull from "branch" on "nickname"
		"""
		self.vcs.pull(nickname, branch)

	def git_push(self, nickname, branch):
		"""
		executes a push to "branch" on "nickname"
		"""
		self.vcs.push(nickname,branch)

	def git_get_submodules(self):
		"""
		returns all submodules in watched directories
		"""
		return self.vcs.get_submodules(include_dir = self.config['local']['watched'])

#singleton hack
_singleton = _Core()
def Core(): 
	"""
	this sould generate a singleton from Core
	"""
	return _singleton


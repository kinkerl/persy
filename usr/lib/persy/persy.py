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


from pyinotify import WatchManager, Notifier, ThreadedNotifier, ProcessEvent, EventsCodes
import os
import sys
from subprocess import Popen
import time
from threading import Thread
import logging , logging.handlers
from configobj import ConfigObj
import threading, time, os, signal, sys, operator
import paramiko
import persygit

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009 Dennis Schwertel"


USERHOME = os.environ["HOME"]
USERHOME_FOLDER = '.persy'
USERHOME_GITREPO = '.git'
CONFIGFILE='config'



DEFAULT_CONFIG="""[general]
username = default
useremail = default 

[local]
sleep = 5
watched =

[remote]
use_remote = False
sleep = 30
hostname = 
path = 
"""
#initialzing the git binding
git = pug.PuG(USERHOME)

#init logging
log = logging.getLogger("")
if not os.path.isdir("%s/%s"%(USERHOME,USERHOME_FOLDER)):
		os.popen("mkdir %s/%s"%(USERHOME,USERHOME_FOLDER))
os.popen("touch %s/%s/default.log"%(USERHOME,USERHOME_FOLDER))
hdlr = logging.handlers.RotatingFileHandler("%s/%s/default.log"%(USERHOME,USERHOME_FOLDER), "a", 1000000, 3)
fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
hdlr.setFormatter(fmt)
log.addHandler(hdlr)
log.setLevel(logging.INFO) #set verbosity to show all messages of severity >= DEBUG

DRY = False
dome = True
lastevent= time.time()

class InterruptWatcher:
	"""taken from http://code.activestate.com/recipes/496735/
	this class solves two problems with multithreaded
	programs in Python, (1) a signal might be delivered
	to any thread (which is just a malfeature) and (2) if
	the thread that gets the signal is waiting, the signal
	is ignored (which is a bug).

	The watcher is a concurrent process (not thread) that
	waits for a signal and the process that contains the
	threads.  See Appendix A of The Little Book of Semaphores.
	http://greenteapress.com/semaphores/

	I have only tested this on Linux.  I would expect it to
	work on the Macintosh and not work on Windows.
	"""
	def __init__(self):
		""" Creates a child thread, which returns.  The parent
		    thread waits for a KeyboardInterrupt and then kills
		    the child thread.
		"""
		self.child = os.fork()
		if self.child == 0:
			return
		else:
			self.watch()

	def watch(self):
		try:
			os.wait()
		except KeyboardInterrupt:
			# I put the capital B in KeyBoardInterrupt so I can
			# tell when the Watcher gets the SIGINT
			print 'KeyBoardInterrupt'
			self.kill()
		sys.exit()

	def kill(self):
		try:
			os.kill(self.child, signal.SIGKILL)
		except OSError: pass



class FileChangeHandler(ProcessEvent):
	def process_IN_MODIFY(self, event):
		log.debug("modify: %s"% event.pathname)
		self.check()

	def process_IN_DELETE_SELF(self, event):
		log.debug("delete_self: %s"% event.pathname)
		self.check()

	def process_IN_DELETE(self, event):
		log.debug("delete: %s"% event.pathname)
		self.check()

	def process_IN_CREATE(self, event):
		log.debug("create: %s"% event.pathname)
		self.check()

	def process_IN_CLOSE_WRITE(self, event):
		log.debug("write: %s"% event.pathname)
		self.check()

	def process_IN_MOVE_SELF(self, event):
		log.debug("move_self: %s"% event.pathname)
		self.check()

	def process_IN_MOVED_TO(self, event):
		log.debug("move_to: %s"% event.pathname)
		self.check()

	def process_IN_MOVED_FROM(self, event):
		log.debug("move_from: %s"% event.pathname)
		self.check()

	def check(self):
		global lastevent
		global dome
		lastevent = time.time()
		dome = True
		


class TheSyncer(Thread):
	def __init__(self, sleep_remote, sleep_local):
		Thread.__init__(self)
		self.sleep_remote = sleep_remote
		self.sleep_local = sleep_local


	def run(self):
		global lastevent
		global dome
		tick = 0

		while True:
			time.sleep(self.sleep_local)
			tick += 1
			log.debug("nap")
			#only do if changed occured (dome==True) and only at least 2 seconds after the last event
			if dome and time.time() - lastevent > self.sleep_local:
				dome = False
				log.info("local commit")
				if not dry and WATCHED:
					git.add(WATCHED)
					git.commit('Backup by me')
					if config['remote']['use_remote']:
						git.push('origin','master')
					git.gc()
			#autopull and push updates every x secs
			if config['remote']['use_remote'] and tick >= (self.sleep_remote/self.sleep_local) :
				tick = 0
				log.info("remote sync")
				if not dry and WATCHED:
					git.pull('origin','master')

def initLocal():
	'''initialises the local repository'''
	if os.path.isdir("%s/%s"%(USERHOME,USERHOME_GITREPO)):
		log.warn("git directory in %s already exists"%USERHOME)
	if not config['general']['username'] or not config['general']['useremail']:
		log.critical('usernae oder useremail not set, cannot create git repository')
		sys.exit(-1)
	git.init()
	git.config('user.name',config['general']['username'])
	git.config('user.email',config['general']['useremail'])

def initRemote():
	'''initialises the remote repository'''
	if not config['remote']['hostname'] or not config['remote']['path']:
		log.critical("no hostname or remote path set, cant init remote server")
		return
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.connect(config['remote']['hostname'] )
	#the follow commands are executet on a remote host. we can not know the path to git, mkdir and cd so we will not replace them with a absolute path 
	stdin1, stdout1, stderr1 = client.exec_command("mkdir -m 700 %s"%config['remote']['path'])
	stdin2, stdout2, stderr2 = client.exec_command("cd %s && git --bare init"%config['remote']['path'])
	client.close()
	if stderr1:
		log.critical(stderr1)
	elif stderr2:
		log.critical(stderr2)
	elif not config['remote']['use_remote']:
		#no errors:so we are save to use the remote
		config['remote']['use_remote'] = True
		config.write()

def syncWithRemote():
	'''Syncs with a remote server'''
	if not config['remote']['hostname'] or not config['remote']['path']:
		log.critical("no hostname or remote path set, cant add remote server")
	else:
		#i dont use clone because of massive errors when using it
		initLocal()
		url = "ssh://%s/%s"%(GIT,config['remote']['hostname'],config['remote']['path'])
		git.remoteAdd('origin',url)
		git.pull('origin','master')
		if not config['remote']['use_remote']:
			config['remote']['use_remote'] = True
			config.write()

def runLocal():
	'''The normal syncer'''
	InterruptWatcher()

	#flags for the filesystem events we want to watch out for
	FLAGS=EventsCodes.ALL_FLAGS
	mask = FLAGS['IN_MODIFY'] | FLAGS['IN_DELETE_SELF']|FLAGS['IN_DELETE'] | FLAGS['IN_CREATE'] | FLAGS['IN_CLOSE_WRITE'] | FLAGS['IN_MOVE_SELF'] | FLAGS['IN_MOVED_TO'] | FLAGS['IN_MOVED_FROM'] # watched events

	wm = WatchManager()
	notifier = Notifier(wm, FileChangeHandler())

	#addin the watched directories
	for watch in WATCHED:
		wdd = wm.add_watch("%s"%(watch), mask, rec=True)

	log.info("Starting persy")
	if not WATCHED:
		log.warn("watching no directories")
	tester = TheSyncer(config['remote']['sleep'], config['local']['sleep'])
	tester.start()
	notifier.loop()

def main(argv):
	args = argv[1:]
	#cli options
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option("--init",action="store_true", default=False, help="initializes the local repository")
	parser.add_option("--initremote",action="store_true", default=False, help="initializes the remote repository")
	parser.add_option("--syncwithremote",action="store_true", default=False, help="syncs with a remote repository")
	parser.add_option("--dry",action="store_true", default=False, help="dry run, no real git actions")
	parser.add_option("--config",action="store_true", default=False, help="needed to change configurations")
	parser.add_option("--path", dest="path", default="", help="path on the server")
	parser.add_option("--hostname", dest="hostname", default="", help="hostname of the remote server")
	parser.add_option("--add_dir", dest="add_dir", default="", help="add local wachted folders")
	(options, args) = parser.parse_args(args)


	#create programdirectory and a default config file
	if not os.path.exists(os.path.join(USERHOME,USERHOME_FOLDER)):
		os.makedirs(os.path.join(USERHOME,USERHOME_FOLDER))
	if not os.path.exists(os.path.join(USERHOME,USERHOME_FOLDER,CONFIGFILE)):
		with open(os.path.join(USERHOME,USERHOME_FOLDER,CONFIGFILE), "w+") as f:
			f.write(DEFAULT_CONFIG)

	#load and set configuration
	global config
	global WATCHED
	global dry

	config = ConfigObj("%s/%s/config"%(USERHOME,USERHOME_FOLDER))
	config['remote']['use_remote'] = config['remote']['use_remote']=='True'
	config['local']['sleep'] = int(config['local']['sleep']or 5) #5 is default
	config['remote']['sleep'] = int(config['remote']['sleep']or 30) #30 is default

	if options.config:
		if options.hostname:
			config['remote']['hostname'] = options.hostname
		if options.path:
			config['remote']['path'] = options.path
		if options.add_dir:
			if type(config['local']['watched']) is str:
				if config['local']['watched']:
					config['local']['watched'] = [config['local']['watched'], options.add_dir]
				else:
					config['local']['watched'] = [options.add_dir,]
			else:
				config['local']['watched'].append(options.add_dir)
		config.write()
		log.info("writing new config")
		sys.exit(0)
	elif options.syncwithremote or options.initremote:
		if options.hostname:
			config['remote']['hostname'] = options.hostname
		if options.path:
			config['remote']['path'] = options.path
		config['remote']['use_remote'] = True
		config.write()

	if type(config['local']['watched']) is str:
		config['local']['watched'] = [config['local']['watched']]
		WATCHED = config['local']['watched']

	log.info("watching over: %s"%WATCHED)

	dry = options.dry
	if dry:
		print "--dry run--"

	if options.init:
		initLocal()
	elif options.initremote:
		initRemote()
	elif options.syncwithremote:
		syncwithRemote()
	else:
		if args:
			print "unknown parameters: %s"%", ".join(args)
			sys.exit(-1)
		runLocal()


if __name__ == '__main__':
	try:
		main(sys.argv)
	except Exception:
		log.exception('Unexpected error')
		raise



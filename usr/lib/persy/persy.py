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
from subprocess import Popen
from threading import Thread
from configobj import ConfigObj
import os
import sys
import time
import logging , logging.handlers
import time, signal, operator
import paramiko
import pug

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009 Dennis Schwertel"

# files and dirs used by persy
USERHOME = os.environ["HOME"]
PERSY_DIR = os.path.join(USERHOME, '.persy') 
GIT_DIR = os.path.join(PERSY_DIR,'git')
CONFIGFILE=os.path.join(PERSY_DIR,'config')
LOGFILE=os.path.join(PERSY_DIR,'default.log')
GITIGNOREFILE=os.path.join(GIT_DIR, 'info','exclude')

#git variables
SERVER_NICK='origin'
BRANCH='master'

DEFAULT_CONFIG="""[general]
name = default
mail = default 

[local]
sleep = 5
watched =

[remote]
use_remote = False
sleep = 30
hostname = 
path = 
"""

lastevent= time.time()
WATCHED=[]
log = ''

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
		lastevent = time.time()


class TheSyncer(Thread):
	def __init__(self, sleep_remote, sleep_local):
		Thread.__init__(self)
		self.sleep_remote = sleep_remote
		self.sleep_local = sleep_local
		self.lastcommit = 0
		self.lastsync = 0


	def run(self):
		global lastevent

		while True:
			time.sleep(self.sleep_local)
			log.debug("nap")
			#only do if changed occured (dome==True) and only at least 2 seconds after the last event
			if not self.lastcommit == lastevent and time.time() - lastevent > self.sleep_local:
				self.lastcommit = lastevent
				log.info("local commit")
				if WATCHED:
					try:
						git.add(WATCHED)
					except Exception as e:
						log.warn(e.__str__())

					try:
						git.commit('Backup by me')
					except Exception as e:
						log.critical(e.__str__())

					try:
						git.gc()
					except Exception as e:
						log.warn(e.__str__())



				
			#autopull and push updates every x secs
			if config['remote']['use_remote'] and time.time() - self.lastsync > self.sleep_remote:
				self.lastsync = time.time()
				log.info("remote sync")
				if WATCHED:
					try:
						git.pull(SERVER_NICK,BRANCH)
					except Exception as e:
						log.critical(e.__str__())

					try:
						git.push(SERVER_NICK,BRANCH)
					except Exception as e:
						log.critical(e.__str__())

def initLocal():
	'''initialises the local repository'''
	if not config.has_key('general') or not config['general'].has_key('name') or not config['general']['name'] :
		log.critical('username not set, cannot create git repository. use "persy --config --name=NAME" to set one')
		sys.exit(-1)
	if not config.has_key('general') or not config['general'].has_key('mail') or not config['general']['mail']:
		log.critical('mail not set, cannot create git repository. use "persy --config --mail=MAIL" to set one')
		sys.exit(-1)
	try:
		git.init()
		git.config('user.name',config['general']['name'])
		git.config('user.email',config['general']['mail'])
		gitignore()
	except Exception as e:
		log.critical(e.__str__())		

def initRemote():
	'''initialises the remote repository'''
	if not config.has_key('remote') or not config['remote'].has_key('hostname') or not config['remote']['hostname']:
		log.critical('no hostname set, cant init remote server. use "persy --config --hostname=HOSTNAME" to set one')
		sys.exit(-1)
	if not config.has_key('remote') or not config['remote'].has_key('path') or not config['remote']['path']:
		log.critical('no remote path set, cant init remote server. use "persy --config --path=PATH" to set one')
		sys.exit(-1)
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.connect(config['remote']['hostname'] )
	#the follow commands are executet on a remote host. we can not know the path to git, mkdir and cd so we will not replace them with a absolute path 
	stdin1, stdout1, stderr1 = client.exec_command("mkdir -m 700 %s"%config['remote']['path'])
	stdin2, stdout2, stderr2 = client.exec_command("cd %s && git --bare init"%config['remote']['path'])
	client.close()
	if stderr1:
		log.warn("error creating dir, maybe it exists already?")
	elif stderr2:
		log.critical("error on remote git init")
	elif not config['remote']['use_remote']:
		#no errors:so we are save to use the remote
		config['remote']['use_remote'] = True
		config.write()
	try:
		git.remoteAdd(SERVER_NICK,"ssh://%s/%s"%(config['remote']['hostname'],config['remote']['path']))
	except Exception as e:
		log.critical(e.__str__())		


def syncWithRemote():
	'''Syncs with a remote server'''
	#i dont use clone because of massive errors when using it
	if not config.has_key('remote') or not config['remote'].has_key('hostname') or not config['remote']['hostname']:
		log.critical('no hostname set, cant init remote server. use "persy --config --hostname=HOSTNAME" to set one')
		sys.exit(-1)
	if not config.has_key('remote') or not config['remote'].has_key('path') or not config['remote']['path']:
		log.critical('no remote path set, cant init remote server. use "persy --config --path=PATH" to set one')
		sys.exit(-1)
	initLocal()
	try:
		git.remoteAdd(SERVER_NICK,"ssh://%s/%s"%(config['remote']['hostname'],config['remote']['path']))
		git.pull(SERVER_NICK,BRANCH)
	except Exception as e:
		log.critical(e.__str__())		

	if not config['remote']['use_remote']:
		config['remote']['use_remote'] = True
		config.write()
	
def gitignore():
	'''creates a file for ignoring unwatched directories so they dont appear in the status (and cant be removed exidently with "git clean")'''
	#list every file in /home/USER
	#add every file and folder (if not already done) to .gitignore if they are not part WATCHED
	current = os.listdir(USERHOME)
	for f in WATCHED:
		if not f.startswith(USERHOME):
			continue #savetycheck
		#strip dir stuff, the +1 is for the file seperator
		f = f[len(USERHOME)+1:]
		if os.sep in f:
			f = f[:f.index(os.sep)]
		if f in current:
			current.remove(f)
	with open(os.path.join(PERSY_DIR,GITIGNOREFILE), "w+") as f:
		for c in current:
			f.write(c+"\n")


def runLocal():
	'''The normal syncer'''
	global WATCHED
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
	log.info("watching over: %s"%WATCHED)
	if not WATCHED:
		log.warn("watching no directories")
	tester = TheSyncer(config['remote']['sleep'], config['local']['sleep'])
	tester.start()
	notifier.loop()

def browse():
	git.command("gitk", stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

def gitlog():
	git.log(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

def gitstatus():
	git.status(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

def main(argv):
	args = argv[1:]

	#init logging
	global log
	log = logging.getLogger("")
	if not os.path.isdir(PERSY_DIR):
		os.makedirs(PERSY_DIR)
	os.popen("touch %s"%LOGFILE)
	hdlr = logging.handlers.RotatingFileHandler(LOGFILE, "a", 1000000, 3)
	fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
	hdlr.setFormatter(fmt)
	log.addHandler(hdlr)
	log.setLevel(logging.INFO) #set verbosity to show all messages of severity >= DEBUG

	#cli options
	from optparse import OptionParser
	parser = OptionParser(usage = "use --start to start the daemon")
	parser.add_option("--start",action="store_true", default=False, help="starts persy")
	parser.add_option("--init",action="store_true", default=False, help="initializes the local repository")
	parser.add_option("--initremote",action="store_true", default=False, help="initializes the remote repository")
	parser.add_option("--syncwithremote",action="store_true", default=False, help="syncs with a remote repository")
	parser.add_option("--browse",action="store_true", default=False, help="start a browser (gitk)")
	parser.add_option("--log",action="store_true", default=False, help="prints git log")
	parser.add_option("--status",action="store_true", default=False, help="prints git status")
	parser.add_option("--ignore",action="store_true", default=False, help="recreates list of all ignored files")
	parser.add_option("--verbose",action="store_true", default=False, help="verbose")

	parser.add_option("--config",action="store_true", default=False, help="needed to change configurations")
	parser.add_option("--name", dest="name", default="", help="username used in commit")
	parser.add_option("--mail", dest="mail", default="", help="useremail used in commit")
	parser.add_option("--path", dest="path", default="", help="path on the server")
	parser.add_option("--hostname", dest="hostname", default="", help="hostname of the remote server")
	parser.add_option("--add_dir", dest="add_dir", default="", help="add local wachted folders")
	(options, args) = parser.parse_args(args)


	#create programdirectory and a default config file
	if not os.path.exists(PERSY_DIR):
		os.makedirs(PERSY_DIR)
	if not os.path.exists(CONFIGFILE):
		with open(CONFIGFILE, "w+") as f:
			f.write(DEFAULT_CONFIG)

	#load and set configuration
	global config
	global WATCHED
	global git

	config = ConfigObj(CONFIGFILE)
	config['remote']['use_remote'] = config['remote']['use_remote']=='True'
	config['local']['sleep'] = int(config['local']['sleep']or 5) #5 is default
	config['remote']['sleep'] = int(config['remote']['sleep']or 30) #30 is default

	if options.config:
		if options.hostname:
			config['remote']['hostname'] = options.hostname
		if options.path:
			config['remote']['path'] = options.path
		if options.username:
			config['general']['name'] = options.name
		if options.useremail:
			config['general']['mail'] = options.mail
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
	
	#initialzing the git binding
	if options.verbose:
		git = pug.PuG(USERHOME, GIT_DIR=GIT_DIR)
	else:
		git = pug.PuG(USERHOME, GIT_DIR=GIT_DIR, stdin=file(os.devnull), stdout=file(os.devnull), stderr=file(os.devnull))

	if options.init:
		initLocal()
	elif options.initremote:
		initRemote()
	elif options.syncwithremote:
		syncWithRemote()
	elif options.browse:
		browse()
	elif options.start:
		runLocal()
	elif options.log:
		gitlog()
	elif options.status:
		gitstatus()
	elif options.ignore:
		gitignore()
	else:
		print "unknown parameters"
		parser.print_help()
		sys.exit(-1)



if __name__ == '__main__':
	try:
		main(sys.argv)
	except Exception as e:
		print 'Unexpected error: ' + e.__str__()
		raise



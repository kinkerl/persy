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

import pynotify
import subprocess

import gtk
import pygtk
#Initializing the gtk's thread engine
#we NEED this because of the STRANGE (F***ING) thread problem with gtk
gtk.gdk.threads_init()

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009 Dennis Schwertel"

# files and dirs used by persy
USERHOME = os.environ["HOME"]
PERSY_DIR = os.path.join(USERHOME, '.persy')
GIT_DIR = os.path.join(PERSY_DIR,'git')
CONFIGFILE=os.path.join(PERSY_DIR,'config')
LOGFILE=os.path.join(PERSY_DIR,'default.log')
LOGFILE_GIT=os.path.join(PERSY_DIR,'git.log')
GITIGNOREFILE=os.path.join(GIT_DIR, 'info','exclude')

VERSION_FILE = '/usr/lib/persy/VERSION'

#git variables
SERVER_NICK='origin'
BRANCH='master'

try:
	VERSION=file(VERSION_FILE).readline()
except Exception:
	VERSION="undefined"

DEFAULT_CONFIG="""[general]
name = default
mail = default

[local]
sleep = 5
watched =
maxfilesize = 
exclude = 

[remote]
use_remote = False
sleep = 30
hostname =
path =
"""
DEFAULT_LOCAL_SLEEP = 5
DEFAULT_REMOTE_SLEEP = 30
DEFAULT_REMOTE_HOSTNAME = ''
DEFAULT_REMOTE_PATH = ''


lastevent= time.time()


log = None
worker = None
notifier = None
statusIcon = None

ICON_IDLE = '/usr/lib/persy/persy_idle.png'
ICON_ERROR = '/usr/lib/persy/persy_error.png'
ICON_OK = '/usr/lib/persy/persy_ok.png'
ICON_WARN = '/usr/lib/persy/persy_warn.png'
ICON_BUSY = '/usr/lib/persy/persy_busy.png'
LOGO = '/usr/lib/persy/persy.png'

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
		self.ignore_time = 60 #one hour
		self.lastcommit = 0
		self.lastsync = 0
		self.lastignore = 0
		self.running = True

	def stop(self):
		self.running = False

	def run(self):
		global lastevent
		self.running = True

		while self.running:
			time.sleep(self.sleep_local)
			log.debug('tick')

			#only do if changed occured (dome==True) and only at least 2 seconds after the last event
			if not self.lastcommit == lastevent and time.time() - lastevent > self.sleep_local:
				self.lastcommit = lastevent
				log.info('local commit')
				if config['local']['watched']:
					log.debug('git ignore')
					self.lastignore = time.time()
					try:
						gitignore()
					except Exception as e:
						log.warn(str(e))


					log.debug('git add')
					try:
						git.add(config['local']['watched'])
					except Exception as e:
						log.warn(str(e))

					log.debug('git commit')
					try:
						git.commit('Backup by me')
					except Exception as e:
						log.critical(str(e))

					#log.debug('git gc')
					#try:
					#	git.gc()
					#except Exception as e:
					#	log.warn(str(e))

			#autopull and push updates every x secs
			if config['remote']['use_remote'] and time.time() - self.lastsync > self.sleep_remote:
				self.lastsync = time.time()
				log.info('remote sync')
				if config['local']['watched']:
					log.debug('git pull')
					try:
						git.pull(SERVER_NICK,BRANCH)
					except Exception as e:
						log.critical(str(e))

					log.debug('git push')
					try:
						git.push(SERVER_NICK,BRANCH)
					except Exception as e:
						log.critical(str(e))
			#start git ignore on a regular basis (ignoring unwatched files)
			if time.time() - self.lastignore >  self.ignore_time:
				self.lastignore = time.time()
				try:
					gitignore()
				except Exception as e:
					log.warn(str(e))


class Talker:
	"""logging, notifications and communications with the outside!"""
	def __init__(self, verbose=False):
		#init logging
		self.log = logging.getLogger("")
		os.popen("touch %s"%LOGFILE)
		hdlr = logging.handlers.RotatingFileHandler(LOGFILE, "a", 1000000, 3)
		fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
		hdlr.setFormatter(fmt)
		self.log.addHandler(hdlr)
		self.verbose = verbose

		#init notify
		self.notifyid = "Persy"
		try:
			pynotify.init(self.notifyid)
		except Exception as e:
			self.log.warn(str(e))

	def setLevel(self, lvl):
		self.log.setLevel(lvl)

	def debug(self, msg, verbose=None):
		self.log.debug(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg


	def info(self, msg, verbose=None):
		self.log.info(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg

	def warn(self, msg, verbose=None):
		self.log.warn(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg
		try:
			pynotify.Notification(self.notifyid, msg, ICON_WARN).show()
		except Exception as e:
			self.log.warn(str(e))

	def critical(msg, verbose=None):
		self.log.critical(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg
		if statusIcon:
			statusIcon.set_from_file(ICON_ERROR)#from_stock(gtk.STOCK_HOME)
		try:
			pynotify.Notification(self.notifyid, msg, ICON_ERROR).show()
		except Exception as e:
			self.log.warn(str(e))



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
		log.critical(str(e))

def initRemote():
	'''initialises the remote repository'''
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.connect(config['remote']['hostname'] )
	# the follow commands are executet on a remote host. we can not know the path to git,
	# mkdir and cd so we will not replace them with a absolute path
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
		log.critical(str(e))


def syncWithRemote():
	'''Syncs with a remote server'''
	#i dont use clone because of massive errors when using it
	initLocal()
	try:
		git.remoteAdd(SERVER_NICK,"ssh://%s/%s"%(config['remote']['hostname'],config['remote']['path']))
		git.pull(SERVER_NICK,BRANCH)
	except Exception as e:
		log.critical(str(e))

	if not config['remote']['use_remote']:
		config['remote']['use_remote'] = True
		config.write()

def gitignore():
	'''creates a file for ignoring unwatched directories so they dont appear in the status (and cant be removed exidently with "git clean")'''
	#list every file in /home/USER
	#add every file and folder (if not already done) to .gitignore if they are not part WATCHED
	current = os.listdir(USERHOME)
	for f in config['local']['watched']:
		if not f.startswith(USERHOME):
			continue #savetycheck
		#strip dir stuff, the +1 is for the file seperator
		f = f[len(USERHOME)+1:]
		if os.sep in f:
			f = f[:f.index(os.sep)]
		if f in current:
			current.remove(f)

		if config['local']['maxfilesize']:
			callcmd = []
			callcmd.append('find')
			callcmd.append(os.path.join(USERHOME,f))
			callcmd.append('-type')
			callcmd.append('f')
			callcmd.append('-size')
			callcmd.append("+" + str(config['local']['maxfilesize']) + "k")
			(stdoutdata, stderrdata) = subprocess.Popen(callcmd, stdout=subprocess.PIPE).communicate()
			for entry in stdoutdata.split("\n"):
				current.append(entry)

	for entry in config['local']['exclude']:
		current.append(entry)

	for entry in config['local']['exclude']:
		current.append(entry)

	with open(os.path.join(PERSY_DIR,GITIGNOREFILE), "w+") as f:
		for c in current:
			f.write(c+"\n")

class Persy_GTK():
	def __init__(self):
		'''The normal syncer'''
		global statusIcon

		log.info("Starting persy")
		log.info("watching over: %s"%config['local']['watched'])

		if not config['local']['watched']:
			log.warn("watching no directories")

		#InterruptWatcher()

		statusIcon = gtk.StatusIcon()
		menu = gtk.Menu()

		menuItem = gtk.CheckMenuItem("start/stop Persy")
		menuItem.set_active(False)
		menuItem.connect('activate',self.persy_toggle)
		menu.append(menuItem)

		menuItem = gtk.CheckMenuItem("sync Remote")
		menuItem.set_active(config['remote']['use_remote'])
		menuItem.connect('activate',self.persy_sync_toggle)
		menu.append(menuItem)


		menuItem = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
		menuItem.get_children()[0].set_label('start gitk')
		menuItem.connect('activate', browse)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_HELP)
		menuItem.get_children()[0].set_label('show Log')
		menuItem.connect('activate', self.showlog)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_HELP)
		menuItem.get_children()[0].set_label('show git Log')
		menuItem.connect('activate', self.showgitlog)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		menuItem.connect('activate', self.about)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menuItem.connect('activate', self.quit_cb, statusIcon)
		menu.append(menuItem)

		statusIcon.set_from_file(ICON_IDLE)
		statusIcon.set_tooltip("Persy")
		statusIcon.connect('popup-menu', self.popup_menu_cb, menu)
		statusIcon.set_visible(True)

		try:
			gtk.main()
		except KeyboardInterrupt:
			log.info("bye!", verbose=True)
			sys.exit(0)
		except Exception as e:
			log.critical(str(e), verbose=True)

	def quit_cb(self, widget, data = None):
		persy_stop()
		if data:
			data.set_visible(False)
		gtk.main_quit()
		sys.exit(0)

	def popup_menu_cb(self, widget, button, time, data = None):
		if data:
			data.show_all()
			data.popup(None, None, None, 3, time)


	def about(self, widget, data = None):
		dlg = gtk.AboutDialog()
		dlg.set_title("About Persy")
		dlg.set_version(VERSION)
		dlg.set_program_name("Persy")
		dlg.set_comments("personal sync")
		dlg.set_authors([
			"Dennis Schwertel <s@digitalkultur.net>"
		])
		dlg.set_icon_from_file(ICON_IDLE)
		dlg.set_logo(gtk.gdk.pixbuf_new_from_file(LOGO))
		def close(w, res):
			if res == gtk.RESPONSE_CANCEL:
				w.hide()
		dlg.connect("response", close)
		dlg.show()

	def showgitlog(self, widget, data = None):
		self.showlog(widget, data, LOGFILE_GIT)

	def showlog(self, widget, data = None, filename=None):
		window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		window.set_resizable(True)
		window.set_title("Persy Log")
		window.set_border_width(0)

		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		textview = gtk.TextView()
		textbuffer = textview.get_buffer()
		sw.add(textview)
		sw.show()
		textview.show()
		window.add(sw)

		if filename:
			infile = open(filename, "r")
		else:
			infile = open(LOGFILE, "r")

		if infile:
			string = infile.read()
			infile.close()
			textbuffer.set_text(string)
		window.set_default_size(500,400)
		window.show()

	def persy_toggle(self, widget, data = None):
		if widget.active:
			persy_start()
		else:
			persy_stop()

	def persy_sync_toggle(self, widget, data = None):
		if widget.active:
			config['remote']['use_remote'] = True
		else:
			config['remote']['use_remote'] = False

		config.write()


def persy_start():
	''' Starts Persy'''
	global worker
	global notifier
	log.info("start working")

	FLAGS=EventsCodes.ALL_FLAGS
	mask = FLAGS['IN_MODIFY'] | FLAGS['IN_DELETE_SELF']|FLAGS['IN_DELETE'] | FLAGS['IN_CREATE'] | FLAGS['IN_CLOSE_WRITE'] | FLAGS['IN_MOVE_SELF'] | FLAGS['IN_MOVED_TO'] | FLAGS['IN_MOVED_FROM'] # watched events

	wm = WatchManager()
	#addin the watched directories
	for watch in config['local']['watched']:
		wdd = wm.add_watch("%s"%(watch), mask, rec=True)

	worker = TheSyncer(config['remote']['sleep'], config['local']['sleep'])
	notifier = ThreadedNotifier(wm, FileChangeHandler())

	worker.start()
	notifier.start()
	if statusIcon:
		statusIcon.set_from_file(ICON_OK)#from_stock(gtk.STOCK_HOME)


def persy_stop():
	'''Stops Persy'''
	global worker
	global notifier
	log.info("stop working")
	if worker:
		try:
			worker.stop()
			worker.join()
		except RuntimeError:
			pass
	if notifier:
		try:
			notifier.stop()
		except RuntimeError:
			pass
		except OSError:
			pass
		except KeyError:
			pass
	if statusIcon:
		statusIcon.set_from_file(ICON_IDLE)#from_stock(gtk.STOCK_HOME)




#just ignore the widget
def browse(wiget=None):
	class Starter(Thread):
		def __init__(self,git):
			Thread.__init__(self)
			self.git = git
		def run(self):
			self.git.command("gitk", stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)
	Starter(git).start()

def gitlog():
	git.log(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

def gitstatus():
	git.status(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

def main(argv):
	args = argv[1:]

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
	parser.add_option("--verbose",action="store_true", default=False, help="print git output to stdout and set loglevel to DEBUG")
	parser.add_option("--actions",action="store_true", default=False, help="computer-readable actions in persy")

	parser.add_option("--config",action="store_true", default=False, help="needed to change configurations")
	parser.add_option("--uname", dest="uname", default="", help="username used in commit")
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

	#init logging
	global log
	log = Talker()
	log.setLevel((logging.INFO,logging.DEBUG)[options.verbose]) #set verbosity to show all messages of severity >= DEBUG

	#load and set configuration
	global config
	global git

	config = ConfigObj(CONFIGFILE)

	if options.config:
		changed = False
		if options.hostname:
			changed = True
			config['remote']['hostname'] = options.hostname
		if options.path:
			changed = True
			config['remote']['path'] = options.path
		if options.uname:
			changed = True
			config['general']['name'] = options.uname
		if options.mail:
			changed = True
			config['general']['mail'] = options.mail
		if options.add_dir:
			changed = True
			if type(config['local']['watched']) is str:
				if config['local']['watched']:
					config['local']['watched'] = [config['local']['watched'], options.add_dir]
				else:
					config['local']['watched'] = [options.add_dir,]
			else:
				config['local']['watched'].append(options.add_dir)
		if changed:
			config.write()
			log.info("writing new config")
		else:
			log.warn("nothing changed, maybe wrong attribute names?")
		sys.exit(0)
	elif options.syncwithremote or options.initremote:
		if options.hostname:
			config['remote']['hostname'] = options.hostname
		if options.path:
			config['remote']['path'] = options.path
		config['remote']['use_remote'] = True
		config.write()


	#config check if everything is ok

	#general name
	if not config['general'].has_key('name') or not config['general']['name']:
		config['general']['name'] = 'default'

	#general mail
	if not config['general'].has_key('mail') or not config['general']['mail']:
		config['general']['name'] = 'mail'

	#local sleep
	if not config['local'].has_key('sleep') or not config['local']['sleep']:
		config['local']['sleep'] = DEFAULT_LOCAL_SLEEP

	if not type(config['local']['sleep']) is int:
		try:
			config['local']['sleep'] = int(config['local']['sleep'])
		except Exception as e:
			config['local']['sleep'] = DEFAULT_LOCAL_SLEEP

	#local watched
	if not config['local'].has_key('watched') or not config['local']['watched']:
		config['local']['watched'] = []

	if type(config['local']['watched']) is str:
		config['local']['watched'] = [config['local']['watched']]

	if not type(config['local']['watched']) is list:
		config['local']['watched'] = []

	#local maxfilesize
	if not config['local'].has_key('maxfilesize') or not type(config['local']['maxfilesize']) is str:
		config['local']['maxfilesize'] = None
	if not type(config['local']['maxfilesize']) is int:
		try:
			config['local']['maxfilesize'] = int(config['local']['maxfilesize'])
		except Exception as e:
			config['local']['maxfilesize'] = None

	#local exclude
	if not config['local'].has_key('exclude'):
		config['local']['exclude']=[]
	if type(config['local']['exclude']) is str:
		config['local']['exclude'] = [config['local']['exclude']]
	if not type(config['local']['exclude']) is list:
		config['local']['exclude'] = []

	#remote use_remote
	if not config['remote'].has_key('use_remote'):
		config['remote']['use_remote'] = False
	if type(config['remote']['use_remote']) is str and config['remote']['use_remote'].lower()  == 'true':
		config['remote']['use_remote'] = True
	if not type(config['remote']['use_remote']) is bool:
		config['remote']['use_remote'] = False

	#remote sleep
	if not config['remote'].has_key('sleep') or not config['remote']['sleep']:
		config['remote']['sleep'] = DEFAULT_REMOTE_SLEEP

	if not type(config['remote']['sleep']) is int:
		try:
			config['remote']['sleep'] = int(config['remote']['sleep'])
		except Exception as e:
			config['remote']['sleep'] = DEFAULT_REMOTE_SLEEP

	#remote hostname
	if not config['remote'].has_key('hostname') or not type(config['remote']['hostname']) is str:
		config['remote']['hostname'] = DEFAULT_REMOTE_HOSTNAME

	#remote path
	if not config['remote'].has_key('path') or not type(config['remote']['path']) is str:
		config['remote']['path'] = DEFAULT_REMOTE_PATH



	#initialzing the git binding
	os.popen("touch %s"%LOGFILE_GIT)
	std = open(LOGFILE_GIT, 'a')
	stdin = None #default stdin
	stdout = std #default stdout
	stderr = std #default stderr
	git = pug.PuG(USERHOME, GIT_DIR=GIT_DIR, stdin=stdin, stdout=stdout, stderr=stderr)

	if options.init:
		initLocal()
	elif options.initremote:
		initRemote()
	elif options.syncwithremote:
		syncWithRemote()
	elif options.browse:
		browse()
	elif options.start:
		Persy_GTK()
	elif options.log:
		gitlog()
	elif options.status:
		gitstatus()
	elif options.ignore:
		gitignore()
	elif options.actions:
		for opt in parser.option_list:
			print opt.get_opt_string(),
		sys.exit(0)
	else:
		log.warn("unknown parameters", verbose=True)
		parser.print_help()
		sys.exit(-1)



if __name__ == '__main__':
	try:
		main(sys.argv)
	except Exception as e:
		print 'Unexpected error: ' + str(e)
		raise



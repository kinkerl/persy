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
	from configobj import ConfigObj
	import os
	import time
	import logging , logging.handlers
	import time, signal, operator
	import paramiko
	import pug
	import pynotify
	import subprocess
	import apt_pkg
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


def getSoftwareVersion(name):
	"""returns the version of a installed software as a String. Returns None if not installed"""
	global aptCache
	if not aptCache:
		print _("using apt-cache to find out about installed apps and versions..")
		apt_pkg.InitConfig()
		apt_pkg.InitSystem()
		aptCache = apt_pkg.GetCache()
	try:
		return aptCache[name].CurrentVer.VerStr
	except Exception as e:
		return None



#Initializing the gtk's thread engine
#we NEED this because of the STRANGE (F***ING) thread problem with gtk
gtk.gdk.threads_init()

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009 Dennis Schwertel"

# files and dirs used by persy
USERHOME = os.environ["HOME"]
PERSY_DIR = os.path.join(USERHOME, '.persy')
GIT_DIR = os.path.join(PERSY_DIR,'git')
GIT_LOCKFILE = os.path.join(GIT_DIR,'index.lock')
CONFIGFILE=os.path.join(PERSY_DIR,'config')
LOGFILE=os.path.join(PERSY_DIR,'default.log')
LOGFILE_GIT=os.path.join(PERSY_DIR,'git.log')
GITIGNOREFILE=os.path.join(GIT_DIR, 'info','exclude')

#path to some files and icons
ICON_IDLE = '/usr/lib/persy/persy.svg'
ICON_OK = '/usr/lib/persy/persy_ok.svg'
ICON_UNSYNCED = '/usr/lib/persy/persy_unsynced.svg'
ICON_UNTRACKED = '/usr/lib/persy/persy_untracked.svg'
ICON_WARN = '/usr/lib/persy/persy_warn.svg'
ICON_ERROR = '/usr/lib/persy/persy_error.svg'
LOGO = '/usr/lib/persy/persy.svg'



#path to the license file
LICENSE_FILE = '/usr/share/common-licenses/GPL-2'

#git variables used by persy
SERVER_NICK='origin'
BRANCH='master'


#aptCache is global for version retrieving
#this is set with the first call of getSoftwareVersion()
aptCache = None

#retrieving the installed version of persy
try:
	VERSION=getSoftwareVersion('persy')
	if not VERSION:
		VERSION=_("undefined")
except Exception as e:
	VERSION=_("undefined")

#the default gui git browser
GITGUI=["gitk", "qgit"] #possible browsers


#xterm terminal
XTERM = "xterm"
#fortune
FORTUNE = "fortune"


#default config entries
DEFAULT_LOCAL_SLEEP = 5
DEFAULT_REMOTE_SLEEP = 300
DEFAULT_REMOTE_HOSTNAME = ''
DEFAULT_REMOTE_PATH = ''

DEFAULT_CONFIG="""# persy configuration file

# general configuration
[general]
# default name and mail for a commit. the default name and mail is fine and is 
# only interessting if you want to sync multiple machines. you can set the name
# on every machine different and get a nice git history
name = default
mail = default

# the prefered gui git browser. possible values are gitk and qgit. if you want 
# more, mail me.
prefgitbrowser=gitk

# use small fortune lines in the git commit description (True/False)
fortune=False


# configurations for the local backup
[local]
# the local sleep delay time in secounds. a backup is only done after this time
# after the last file action
sleep = %i

# a coma seperated list auf the files and directories, persy is syncing
watched =

# the maximal allowed filesize for the synced files in bytes
maxfilesize = 

# a regular expression to match against every file. matches are excuded
exclude = 


# configuration for a remote backup/sync
[remote]
# backup and sync to a remote host (False/True)
use_remote = False

# the interval in which a sync happens in seconds
sleep = %if

# the host adress of the remote server as ip or name
hostname = %s

# the absolute path on the remote server to the git repository
path = %s
"""%(DEFAULT_LOCAL_SLEEP, DEFAULT_REMOTE_SLEEP, DEFAULT_REMOTE_HOSTNAME, DEFAULT_REMOTE_PATH)

#the last filechange event
lastevent= time.time()

#global stuff
log = None
worker = None
notifier = None
statusIcon = None




class FileChangeHandler(ProcessEvent):
	'''Callback for the pyinotify library. 
Accepts events from the library if a file changes and sets the lastevent time and sets the untracked_changes flag to True'''

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
			log.debug("%s: %s"% (typ, event.path))
		except Exception as e:
			log.warn(_("error with %s event. maybe problem with path?")%typ)
			log.warn(str(e))
		
		lastevent = time.time()
		log.untracked_changes(True)


class TheSyncer(Thread):
	'''The syncing logic.
executing the local commits, the remote pulls/pushs and the updating of the ignore file after self.ignore_time minutes.
'''

	def __init__(self, sleep_remote, sleep_local):
		Thread.__init__(self)
		self.sleep_remote = sleep_remote
		self.sleep_local = sleep_local
		self.ignore_time = 60 #one hour
		self.lastcommit = 0
		self.lastsync = 0
		self.lastignore = 0
		self.running = True
		self.onetimesync = False #if set will sync one time!
		self.errorlocalcounter = 0
		self.errorremotecounter = 0
		
	def setonetimesync(self):
		self.onetimesync = True

	def generateCommitMessage(self):
		'''generates a nice commit message'''
		commitDesc = 'Backup by me'
		if config['general']['fortune']:
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
						self.errorlocalcounter += 1
						if self.errorlocalcounter > 1:
							log.warn(str(e))


					log.debug('git add')
					try:
						git.add(config['local']['watched'])
					except Exception as e:
						self.errorlocalcounter += 1
						if self.errorlocalcounter > 1:
							log.warn(str(e))

					log.debug('git commit')
					try:
						git.commit(self.generateCommitMessage())
					except Exception as e:
						self.errorlocalcounter += 1
						if self.errorlocalcounter > 1:						
							log.critical(str(e))
					else: 
						self.errorlocalcounter = 0					
						log.unsynced_changes(True)

			#autopull and push updates every x secs
			if self.onetimesync or (config['remote']['use_remote'] and time.time() - self.lastsync > self.sleep_remote):
				self.onetimesync = False
				self.lastsync = time.time()
				log.info('remote sync')
				if config['local']['watched']:
					okcounter = 0
					log.debug('git pull')
					try:
						git.pull(SERVER_NICK,BRANCH)
					except Exception as e:
						self.errorremotecounter += 1
						if self.errorremotecounter > 2:
							log.critical(str(e))
					else:
						okcounter += 1

					log.debug('git push')
					try:
						git.push(SERVER_NICK,BRANCH)
					except Exception as e:
						self.errorremotecounter += 1
						if self.errorremotecounter > 2:					
							log.critical(str(e))
					else:
						okcounter += 1

					if okcounter >= 2:
						self.errorlocalcounter = 0	
						log.unsynced_changes(False)
			#start git ignore on a regular basis (ignoring unwatched files)
			if time.time() - self.lastignore >  self.ignore_time:
				self.lastignore = time.time()
				try:
					gitignore()
				except Exception as e:
					log.warn(str(e))


class Talker:
	'''logging, notifications and communications with the outside!
if the critical or warning function is called, the Talker goes into an "error occured" mode:
The statusicon will not change to any other state until this errorstate is reseted.
'''
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

		self.resetError()

	def resetError(self):
		'''resets the error state'''
		self.error = False

	def untracked_changes(self, uc):
		'''sets or unsets the untracked_changes status -> sets the status icon'''
		if not self.error:
			if uc:
				if statusIcon:
					statusIcon.set_from_file(ICON_UNTRACKED)
			else:
				if statusIcon:
					statusIcon.set_from_file(ICON_OK)

	def unsynced_changes(self, uc):
		'''sets or unsets the unsynced_changes status -> sets the status icon'''
		if not self.error:
			if uc:
				if statusIcon:
					statusIcon.set_from_file(ICON_UNSYNCED)
			else:
				if statusIcon:
					statusIcon.set_from_file(ICON_OK)

	def setLevel(self, lvl):
		'''set the logging level. see logging.INFO,logging.DEBUG... for more information'''
		self.log.setLevel(lvl)

	def debug(self, msg, verbose=None):
		'''logs a debug message'''
		self.log.debug(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg

	def info(self, msg, verbose=None):
		'''logs a info message'''
		self.log.info(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg

	def warn(self, msg, verbose=None):
		''' logs a warning message, changes the status icon, fires a notification and sets the error state'''
		self.error = True
		self.log.warn(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg
		if statusIcon:
			statusIcon.set_from_file(ICON_WARN)#from_stock(gtk.STOCK_HOME)
		try:
			pynotify.Notification(self.notifyid, msg, ICON_WARN).show()
		except Exception as e:
			self.log.warn(str(e))

	def critical(self, msg, verbose=None):
		''' logs a critical message, changes the status icon, fires a notification and sets the error state'''
		self.error = True
		self.log.critical(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg
		if statusIcon:
			statusIcon.set_from_file(ICON_ERROR)#from_stock(gtk.STOCK_HOME)
		try:
			pynotify.Notification(self.notifyid, msg, ICON_ERROR).show()
		except Exception as e:
			self.log.warn(str(e))

class Persy_GTK():
	'''the gtk main loop and the status icon'''

	def __init__(self, start=False):
		global statusIcon

		log.info("Starting persy")
		log.info("watching over: %s"%config['local']['watched'])

		if not config['local']['watched']:
			log.warn("watching no directories")

		#InterruptWatcher()

		statusIcon = gtk.StatusIcon()
		menu = gtk.Menu()

		menuItem = gtk.CheckMenuItem(_("start/stop Persy"))
		menuItem.set_active(start)
		menuItem.connect('activate',self.persy_toggle)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
		menuItem.get_children()[0].set_label(_('sync Remote'))
		menuItem.connect('activate', self.persy_sync_remote)
		menu.append(menuItem)

		menuItem = gtk.CheckMenuItem(_("auto sync Remote"))
		menuItem.set_active(config['remote']['use_remote'])
		menuItem.connect('activate',self.persy_sync_toggle)
		menu.append(menuItem)

		if config['general']['prefgitbrowser'] != "":
			menuItem = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
			menuItem.get_children()[0].set_label(_("start %s")%config['general']['prefgitbrowser'])
			menuItem.connect('activate', browse)
			menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
		menuItem.get_children()[0].set_label(_('optimize'))
		menuItem.connect('activate', self.optimize)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_HELP)
		menuItem.get_children()[0].set_label(_('show Log'))
		menuItem.connect('activate', self.showlog)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_HELP)
		menuItem.get_children()[0].set_label(_('show git Log'))
		menuItem.connect('activate', self.showgitlog)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		menuItem.connect('activate', self.about)
		menu.append(menuItem)

		menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menuItem.connect('activate', self.quit_cb, statusIcon)
		menu.append(menuItem)

		statusIcon.set_from_file(ICON_IDLE)
		watched = _('watching over:')+' \n'
		for x in config['local']['watched']:
			watched += "- " + x + '\n'
		watched = watched[:-1]
		statusIcon.set_tooltip(watched)
		statusIcon.connect('popup-menu', self.popup_menu_cb, menu)
		statusIcon.set_visible(True)

		if start:
			persy_start()
		try:
			gtk.main()
		except KeyboardInterrupt:
			log.info("bye!", verbose=True)
			sys.exit(0)
		except Exception as e:
			log.critical(str(e), verbose=True)

	def quit_cb(self, widget, data = None):
		'''stopts persy'''
		persy_stop()
		if data:
			data.set_visible(False)
		gtk.main_quit()
		sys.exit(0)

	def popup_menu_cb(self, widget, button, time, data = None):
		'''show the rightclick menu'''
		if data:
			data.show_all()
			data.popup(None, None, None, 3, time)


	def about(self, widget, data = None):
		'''show the about dialog'''
		dlg = gtk.AboutDialog()
		dlg.set_title(_("About Persy"))
		dlg.set_version(VERSION)
		dlg.set_program_name("Persy")
		dlg.set_comments(_("personal sync"))
		try:
			dlg.set_license(open(LICENSE_FILE).read())
		except Exception as e:
			dlg.set_license(_("Sorry, i have a problem finding/reading the licence"))
			log.warn(str(e))

		dlg.set_authors([
			"Dennis Schwertel <s@digitalkultur.net>"
		])
		dlg.set_icon_from_file(LOGO)
		dlg.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(LOGO, 128, 128))
		def close(w, res):
			if res == gtk.RESPONSE_CANCEL:
				w.hide()
		dlg.connect("response", close)
		dlg.show()

	def showgitlog(self, widget, data = None):
		'''displays the git log'''
		self.showlog(widget, data, LOGFILE_GIT)

	def showlog(self, widget, data = None, filename=None):
		'''displays the default.log'''
		'''executes git-gc'''
		log.debug('show log')
		class Starter(Thread):
			def __init__(self):
				Thread.__init__(self)
			def run(self):
				try:
					callcmd = []
					callcmd.append(XTERM)
					callcmd.append('-e')
					callcmd.append('tail')
					callcmd.append('-n')
					callcmd.append('100')
					callcmd.append('-f')
	
					if filename:
						callcmd.append(filename)
					else:
						callcmd.append(LOGFILE)

					(stdoutdata, stderrdata) = subprocess.Popen(callcmd, stdout=subprocess.PIPE).communicate()
				except Exception as e:
					log.warn(str(e), verbose=True)

		try:
			Starter().start()
		except Exception as e:
			log.warn(str(e), verbose=True)



	def persy_toggle(self, widget, data = None):
		'''toggles the state of persy (start/stop)'''
		if widget.active:
			persy_start()
		else:
			persy_stop()

	def persy_sync_remote(self, widget, data = None):
		global worker
		log.info("onetimesync")
		if worker:
			try:
				worker.setonetimesync()
			except RuntimeError:
				pass

	def persy_sync_toggle(self, widget, data = None):
		'''toggles the sync state (use_remote) of persy (True/False) '''
		if widget.active:
			config['remote']['use_remote'] = True
		else:
			config['remote']['use_remote'] = False

		config.write()

	def optimize(self, widget, data = None):
		'''calls the optimize function'''
		optimize()
		


def initLocal():
	'''initialises the local repository'''
	if not config.has_key('general') or not config['general'].has_key('name') or not config['general']['name'] :
		log.critical(_('username not set, cannot create git repository. use "persy --config --name=NAME" to set one'), verbose=True)
		sys.exit(-1)
	if not config.has_key('general') or not config['general'].has_key('mail') or not config['general']['mail']:
		log.critical(_('mail not set, cannot create git repository. use "persy --config --mail=MAIL" to set one'), verbose=True)
		sys.exit(-1)

	log.info(_("initialising local repository..."), verbose=True)
	
	try:
		git.init()
		git.config('user.name',config['general']['name'])
		git.config('user.email',config['general']['mail'])
		gitignore()
	except Exception as e:
		log.critical(str(e), verbose=True)
	else:
		log.info(_("done"), verbose=True)

def initRemote():
	'''initialises the remote repository'''

	log.info(_("initialising and adding remote repository..."), verbose=True)
	try:	
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		client.connect(config['remote']['hostname'] )
		# the follow commands are executet on a remote host. we can not know the path to git,
		# mkdir and cd so we will not replace them with a absolute path
		stdin1, stdout1, stderr1 = client.exec_command("mkdir -m 700 %s"%config['remote']['path'])
		stdin2, stdout2, stderr2 = client.exec_command("cd %s && git --bare init"%config['remote']['path'])
		client.close()
		if stderr1:
			log.warn(_("error creating dir, maybe it exists already?"), verbose=True)
		elif stderr2:
			log.critical(_("error on remote git init"), verbose=True)
		elif not config['remote']['use_remote']:
			#no errors:so we are save to use the remote
			config['remote']['use_remote'] = True
			config.write()
		git.remoteAdd(SERVER_NICK,"ssh://%s/%s"%(config['remote']['hostname'],config['remote']['path']))
	except Exception as e:
		log.critical(str(e), verbose=True)
	else:
		log.info(_("done"), verbose=True)


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
		#if not f.startswith(USERHOME):
		if f.startswith(USERHOME): #if absolute path
		#strip dir stuff, the +1 is for the file seperator
			f = f[len(USERHOME)+1:]
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

	with open(os.path.join(PERSY_DIR,GITIGNOREFILE), "w+") as f:
		for c in current:
			f.write(c+"\n")


def optimize():
	'''executes git-gc'''
	log.info('starting optimization', verbose=True)
	class Starter(Thread):
		def __init__(self,git):
			Thread.__init__(self)
			self.git = git
		def run(self):
			try:
				log.debug('git gc')
				self.git.gc()
			except Exception as e:
				log.warn(str(e), verbose=True)

	try:
		Starter(git).start()
	except Exception as e:
		log.warn(str(e), verbose=True)



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

	log.resetError()
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




#just ignore the widget if started from cli
def browse(wiget=None):
	'''starts the default git browser'''
	class Starter(Thread):
		def __init__(self,git):
			Thread.__init__(self)
			self.git = git
		def run(self):
			self.git.command(config['general']['prefgitbrowser'], stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)
	Starter(git).start()

def gitlog():
	'''executes the git-log command'''
	git.log(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

def gitstatus():
	'''executes the git-status command'''
	git.status(stdout=sys.stdout, stdin=sys.stdin, stderr=sys.stderr)

def main(argv):
	args = argv[1:]

	#change in the userhome for all actions
	os.chdir(USERHOME)

	#cli options
	from optparse import OptionParser
	parser = OptionParser(usage = _("use --start to start the daemon"))
	parser.add_option("--start",action="store_true", default=False, help=_("starts persy"))
	parser.add_option("--init",action="store_true", default=False, help=_("initializes the local repository"))
	parser.add_option("--initremote",action="store_true", default=False, help=_("initializes the remote repository"))
	parser.add_option("--syncwithremote",action="store_true", default=False, help=_("syncs with a remote repository"))
	parser.add_option("--browse",action="store_true", default=False, help=_("start a browser (gitk)"))
	parser.add_option("--log",action="store_true", default=False, help=_("prints git log"))
	parser.add_option("--status",action="store_true", default=False, help=_("prints git status"))
	parser.add_option("--ignore",action="store_true", default=False, help=_("recreates list of all ignored files"))
	parser.add_option("--verbose",action="store_true", default=False, help=_("print git output to stdout and set loglevel to DEBUG"))
	parser.add_option("--actions",action="store_true", default=False, help=_("computer-readable actions in persy"))
	parser.add_option("--optimize",action="store_true", default=False, help=_("optimizes the stored files. saves space and improves performance"))

	parser.add_option("--config",action="store_true", default=False, help=_("needed flag to change configurations"))
	parser.add_option("--uname", dest="uname", default="", help=_("username used in commit"))
	parser.add_option("--mail", dest="mail", default="", help=_("useremail used in commit"))
	parser.add_option("--path", dest="path", default="", help=_("path on the server"))
	parser.add_option("--hostname", dest="hostname", default="", help=_("hostname of the remote server"))
	parser.add_option("--add_dir", dest="add_dir", default="", help=_("add local wachted folders"))
	(options, args) = parser.parse_args(args)

	#create programdirectory and a default config file
	if not os.path.exists(PERSY_DIR):
		os.makedirs(PERSY_DIR)
	if not os.path.exists(CONFIGFILE):
		with open(CONFIGFILE, "w+") as f:
			f.write(DEFAULT_CONFIG)

	#init logging
	global log
	log = Talker(options.verbose) #verbose = print ALL output to stdout
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
			log.warn(_("nothing changed, maybe wrong attribute names?"))
		sys.exit(0)
	elif options.syncwithremote or options.initremote:
		if options.hostname:
			config['remote']['hostname'] = options.hostname
		if options.path:
			config['remote']['path'] = options.path
		config['remote']['use_remote'] = True
		config.write()


	#config check if everything is ok
	#================================
	#general name
	if not config['general'].has_key('name') or not config['general']['name']:
		config['general']['name'] = 'default'

	#general mail
	if not config['general'].has_key('mail') or not config['general']['mail']:
		config['general']['name'] = 'mail'
	
	#general fortune
	if not config['general'].has_key('fortune'):
		config['general']['fortune'] = False
	if type(config['general']['fortune']) is str and config['general']['fortune'].lower()  == 'true':
		config['general']['fortune'] = True
	if not type(config['general']['fortune']) is bool:
		config['general']['fortune'] = False

	#general gitgui
	if not config['general'].has_key('prefgitbrowser'):
		if getSoftwareVersion(GITGUI[0]):
			config['general']['prefgitbrowser'] = GITGUI[0]
		elif getSoftwareVersion(GITGUI[1]):
			config['general']['prefgitbrowser'] = GITGUI[1]
		else:
			log.critical(_("gitk and qgit is not installed, this should not happen!"))
			config['general']['prefgitbrowser'] = ""
	if type(config['general']['prefgitbrowser']) is str:
		if config['general']['prefgitbrowser'].lower() in GITGUI and getSoftwareVersion(config['general']['prefgitbrowser']):
			config['general']['prefgitbrowser'] = config['general']['prefgitbrowser'].lower()
		else:
			if getSoftwareVersion(GITGUI[0]):
				config['general']['prefgitbrowser'] = GITGUI[0]
			elif getSoftwareVersion(GITGUI[1]):
				config['general']['prefgitbrowser'] = GITGUI[1]
			else:
				log.warn(_("gitk and qgit is not installed, this should not happen!"))
				config['general']['prefgitbrowser'] = ""
	if not type(config['general']['prefgitbrowser']) is str:
		log.warn(_("the config for the prefered git browser is broken?"))
		config['general']['prefgitbrowser'] = ""


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
	#===========================
	#if persy is interrupted while git was running, a git.lockfile may be present. we have to remove it!
	if os.path.exists(GIT_LOCKFILE):
		try: 
			os.remove(GIT_LOCKFILE)
		except Exception as e:
			log.warn(str(e))
		else:
			log.warn(_("removed git lock file"))

	#init pug
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
	elif options.log:
		gitlog()
	elif options.status:
		gitstatus()
	elif options.ignore:
		gitignore()
	elif options.optimize:
		optimize()
	elif options.actions:
		#this i used for cli completion
		for opt in parser.option_list:
			print opt.get_opt_string(),
		sys.exit(0)
	else:
		#check if all the icons are present, just warn is something is missing
		filestocheck = (ICON_IDLE,ICON_OK,ICON_UNSYNCED,ICON_UNTRACKED,ICON_WARN,ICON_ERROR, LOGO)
		fileresults = map(os.path.exists,filestocheck)
		i = 0 
		for fileresult in fileresults:
			if not fileresult:
				log.warn(_("%s file is missing!") % filestocheck[i])
			i += 1


		#START!
		Persy_GTK(options.start)


if __name__ == '__main__':
	try:
		main(sys.argv)
	except Exception as e:
		print 'Unexpected error: ' + str(e)
		raise



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
	from persy_core import Core
	from persy_gtk import PersyGtk
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





#Initializing the gtk's thread engine
#we NEED this because of the STRANGE (F***ING) thread problem with gtk
gtk.gdk.threads_init()

__author__ = "Dennis Schwertel"
__copyright__ = "Copyright (C) 2009 Dennis Schwertel"








class Talker:
	'''logging, notifications and communications with the outside!
if the critical or warning function is called, the Talker goes into an "error occured" mode:
The statusicon will not change to any other state until this errorstate is reseted.
'''
	def __init__(self, config, verbose=False):
		self.config = config
		#init logging
		self.log = logging.getLogger("")
		os.popen("touch %s"%self.config.getAttribute('LOGFILE'))
		hdlr = logging.handlers.RotatingFileHandler(self.config.getAttribute('LOGFILE'), "a", 1000000, 3)
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

	def setStatusIcon(self, icon):
		self.statusIcon = icon

	def setStart(self):
		if self.statusIcon:
			self.statusIcon.set_from_file(self.config.getAttribute('ICON_OK'))#from_stock(gtk.STOCK_HOME)

	def setStop(self):
		if self.statusIcon:
			self.statusIcon.set_from_file(self.config.getAttribute('ICON_IDLE'))#from_stock(gtk.STOCK_HOME)

	def resetError(self):
		'''resets the error state'''
		self.error = False

	def untracked_changes(self, uc):
		'''sets or unsets the untracked_changes status -> sets the status icon'''
		if not self.error:
			if uc:
				if self.statusIcon:
					self.statusIcon.set_from_file(self.config.getAttribute('ICON_UNTRACKED'))
			else:
				if self.statusIcon:
					self.statusIcon.set_from_file(self.config.getAttribute('ICON_OK'))

	def unsynced_changes(self, uc):
		'''sets or unsets the unsynced_changes status -> sets the status icon'''
		if not self.error:
			if uc:
				if self.statusIcon:
					self.statusIcon.set_from_file(self.config.getAttribute('ICON_UNSYNCED'))
			else:
				if self.statusIcon:
					self.statusIcon.set_from_file(self.config.getAttribute('ICON_OK'))

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
		if self.statusIcon:
			self.statusIcon.set_from_file(self.config.getAttribute('ICON_WARN'))#from_stock(gtk.STOCK_HOME)
		try:
			pynotify.Notification(self.notifyid, msg, self.config.getAttribute('ICON_WARN')).show()
		except Exception as e:
			self.log.warn(str(e))

	def critical(self, msg, verbose=None):
		''' logs a critical message, changes the status icon, fires a notification and sets the error state'''
		self.error = True
		self.log.critical(msg)
		if verbose == True or (verbose == None and self.verbose):
			print msg
		if self.statusIcon:
			self.statusIcon.set_from_file(self.config.getAttribute('ICON_ERROR'))#from_stock(gtk.STOCK_HOME)
		try:
			pynotify.Notification(self.notifyid, msg, self.config.getAttribute('ICON_ERROR')).show()
		except Exception as e:
			self.log.warn(str(e))






def main(argv):
	global log
	args = argv[1:]

	config =  PersyConfig()

	#change in the userhome for all actions
	os.chdir(config.getAttribute('USERHOME'))

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
	if not os.path.exists(config.getAttribute('PERSY_DIR')):
		os.makedirs(config.getAttribute('PERSY_DIR'))




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
			self.config.write()
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
		self.config.write()


	log = Talker(config, options.verbose) #verbose = print ALL output to stdout
	log.setLevel((logging.INFO,logging.DEBUG)[options.verbose]) #set verbosity to show all messages of severity >= DEBUG

	core = Core()
	core.init(config, log)



	if options.init:
		core.initLocal()
	elif options.initremote:
		core.initRemote()
	elif options.syncwithremote:
		core.syncWithRemote()
	elif options.browse:
		core.browse()
	elif options.log:
		core.gitlog()
	elif options.status:
		core.gitstatus()
	elif options.ignore:
		core.gitignore()
	elif options.optimize:
		core.optimize()
	elif options.actions:
		#this i used for cli completion
		for opt in parser.option_list:
			print opt.get_opt_string(),
		sys.exit(0)
	else:
		#check if all the icons are present, just warn is something is missing
		filestocheck = (config.getAttribute('ICON_IDLE'),config.getAttribute('ICON_OK'),
			config.getAttribute('ICON_UNSYNCED'),config.getAttribute('ICON_UNTRACKED'),
			config.getAttribute('ICON_WARN'), config.getAttribute('ICON_ERROR'), 
			config.getAttribute('LOGO'))
		fileresults = map(os.path.exists,filestocheck)
		i = 0 
		for fileresult in fileresults:
			if not fileresult:
				log.warn(_("%s file is missing!") % filestocheck[i])
			i += 1


		#START!
		pgtk = PersyGtk()
		pgtk.init(core, config, log, options.start)


if __name__ == '__main__':
	try:
		main(sys.argv)
	except Exception as e:
		print 'Unexpected error: ' + str(e)
		raise



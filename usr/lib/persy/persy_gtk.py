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
	import os
	import time
	import logging , logging.handlers
	import time, signal, operator
	import paramiko
	import pug
	import pynotify
	import subprocess
	import gtk
	import gtk.glade
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

def striplist(l):
	'''helper function to strip lists'''
	return ([x.strip() for x in l])

class PersyGtkMenu():
	def __init__(self, config, log, gtkcore):
		self.config = config
		self.log = log
		self.gtkcore = gtkcore

		self.wTree = gtk.glade.XML(self.config.getAttribute('GLADEFILE'), 'window1')
		self.wTree.get_widget("window1").set_icon_from_file(self.config.getAttribute('LOGO'))
		self.wTree.get_widget("window1").set_title(_("persy settings"))


		self.wTree.get_widget("buttonSave").connect("clicked", self.save)
		self.wTree.get_widget("buttonSave").set_label(_("save"))


		textGeneralName = self.wTree.get_widget('labelGeneral')
		textGeneralName.set_label(_("general"))

		textGeneralName = self.wTree.get_widget('labelLocal')
		textGeneralName.set_label(_("local"))

		textGeneralName = self.wTree.get_widget('labelRemote')
		textGeneralName.set_label(_("remote"))

		textGeneralName = self.wTree.get_widget('labelDevel')
		textGeneralName.set_label(_("development/admin"))

		#general configuration
		textGeneralName = self.wTree.get_widget('labelGeneralName')
		textGeneralName.set_label(_("name"))

		textGeneralName = self.wTree.get_widget('textGeneralName')
		textGeneralName.set_text(config['general']['name'])
		textGeneralName.set_tooltip_text(_("the name used in git. the default should be fine"))


		textGeneralName = self.wTree.get_widget('labelGeneralMail')
		textGeneralName.set_label(_("mail"))

		textGeneralName = self.wTree.get_widget('textGeneralMail')
		textGeneralName.set_text(config['general']['mail'])
		textGeneralName.set_tooltip_text(_("the mail used in git. the default should be fine"))

		textGeneralName = self.wTree.get_widget('labelGeneralFortune')
		textGeneralName.set_label(_("fortune"))

		textGeneralName = self.wTree.get_widget('checkGeneralFortune')
		textGeneralName.set_active(config['general']['fortune'])
		textGeneralName.set_tooltip_text(_("use fortune messages in the git commit message. disabled is fine."))


		textGeneralName = self.wTree.get_widget('labelGeneralGitBrowser')
		textGeneralName.set_label(_("git browser"))

		textGeneralName = self.wTree.get_widget('textGeneralGitBrowser')
		textGeneralName.set_text(config['general']['prefgitbrowser'])
		textGeneralName.set_tooltip_text(_("the prefered git browser for browsing the local persy repository"))

		#local configuration
		textGeneralName = self.wTree.get_widget('labelLocalSleep')
		textGeneralName.set_label(_("sleep"))

		textGeneralName = self.wTree.get_widget('spinLocalSleep')
		textGeneralName.set_value(int(config['local']['sleep']))
		textGeneralName.set_tooltip_text(_("time in seconds to wait for an action after a filechange occurs"))


		textGeneralName = self.wTree.get_widget('labelLocalWatched')
		textGeneralName.set_label(_("watched"))

		textGeneralName = self.wTree.get_widget('textLocalWatched')
		textGeneralName.set_text(", ".join(config['local']['watched']))
		textGeneralName.set_tooltip_text(_("the folders and directories watched in persy. this is a comma seperated list"))

		textGeneralName = self.wTree.get_widget('labelLocalFilesize')
		textGeneralName.set_label(_("max filesize"))

		textGeneralName = self.wTree.get_widget('spinLocalFilesize')
		textGeneralName.set_value(int(config['local']['maxfilesize']))
		textGeneralName.set_tooltip_text(_("the maximal allowed filesize in bytes used for files in persy. all files larger than this value will be ignored"))


		textGeneralName = self.wTree.get_widget('labelLocalExclude')
		textGeneralName.set_label(_("exclude"))

		textGeneralName = self.wTree.get_widget('textLocalExclude')
		textGeneralName.set_text(", ".join(config['local']['exclude']))
		textGeneralName.set_tooltip_text(_("exclude files which map to one of the regular expressions. the expressions are seperated by a comma"))

		#remote configuration
		textGeneralName = self.wTree.get_widget('labelRemoteUse')
		textGeneralName.set_label(_("use remote"))

		textGeneralName = self.wTree.get_widget('checkRemoteUse')
		textGeneralName.set_active(config['remote']['use_remote'])
		textGeneralName.set_tooltip_text(_("synchronize to the remote server"))

		textGeneralName = self.wTree.get_widget('labelRemoteSleep')
		textGeneralName.set_label(_("sleep"))

		textGeneralName = self.wTree.get_widget('spinRemoteSleep')
		textGeneralName.set_value(int(config['remote']['sleep']))
		textGeneralName.set_tooltip_text(_("interval in seconds in which a synchronization with the remote host occurs"))


		textGeneralName = self.wTree.get_widget('labelRemoteHostname')
		textGeneralName.set_label(_("hostname"))

		textGeneralName = self.wTree.get_widget('textRemoteHostname')
		textGeneralName.set_text(config['remote']['hostname'])
		textGeneralName.set_tooltip_text(_("the hostname of the remote server"))

		textGeneralName = self.wTree.get_widget('labelRemotePath')
		textGeneralName.set_label(_("path"))

		textGeneralName = self.wTree.get_widget('textRemotePath')
		textGeneralName.set_text(config['remote']['path'])
		textGeneralName.set_tooltip_text(_("the path to the git repository on the remote server"))

		#devel
		textGeneralName = self.wTree.get_widget('labelGitBrowser')
		textGeneralName.set_label(_("start a git browser"))
		self.wTree.get_widget("buttonBrowse").connect("clicked", self.gtkcore.browse)
		self.wTree.get_widget("buttonBrowse").set_label(_("start"))

		textGeneralName = self.wTree.get_widget('labelShowLog')
		textGeneralName.set_label(_("show log"))
		self.wTree.get_widget("buttonLog").connect("clicked", self.gtkcore.showlog)
		self.wTree.get_widget("buttonLog").set_label(_("show"))

		textGeneralName = self.wTree.get_widget('labelShowGitLog')
		textGeneralName.set_label(_("show git log"))
		self.wTree.get_widget("buttonGitLog").connect("clicked", self.gtkcore.showgitlog)
		self.wTree.get_widget("buttonGitLog").set_label(_("show"))

		textGeneralName = self.wTree.get_widget('labelInitLocal')
		textGeneralName.set_label(_("init local (beware)"))
		self.wTree.get_widget("buttonInitLocal").connect("clicked", self.gtkcore.initLocal)
		self.wTree.get_widget("buttonInitLocal").set_label(_("start"))

		textGeneralName = self.wTree.get_widget('labelInitRemote')
		textGeneralName.set_label(_("init remote (beware)"))
		self.wTree.get_widget("buttonInitRemote").connect("clicked", self.gtkcore.initRemote)
		self.wTree.get_widget("buttonInitRemote").set_label(_("start"))

		textGeneralName = self.wTree.get_widget('labelSyncRemote')
		textGeneralName.set_label(_("sync with remote (beware)"))
		self.wTree.get_widget("buttonSyncRemote").connect("clicked", self.gtkcore.syncWithRemote)
		self.wTree.get_widget("buttonSyncRemote").set_label(_("start"))

		
	def save(self, widget, data=None):
		self.log.info("saving configuration")
		#general configuration
		textGeneralName = self.wTree.get_widget('textGeneralName')
		self.config['general']['name'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('textGeneralMail')
		self.config['general']['mail'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('checkGeneralFortune')
		self.config['general']['fortune'] = textGeneralName.get_active()

		textGeneralName = self.wTree.get_widget('textGeneralGitBrowser')
		self.config['general']['prefgitbrowser'] = textGeneralName.get_text()


		#local configuration
		textGeneralName = self.wTree.get_widget('spinLocalSleep')
		self.config['local']['sleep'] = int(textGeneralName.get_value())
		#textGeneralName.set_value(-1)

		textGeneralName = self.wTree.get_widget('textLocalWatched')
		self.config['local']['watched'] = striplist(textGeneralName.get_text().split(','))
		
		textGeneralName = self.wTree.get_widget('spinLocalFilesize')
		self.config['local']['maxfilesize'] = int(textGeneralName.get_value())
		#textGeneralName.set_value(-1)

		textGeneralName = self.wTree.get_widget('textLocalExclude')
		self.config['local']['exclude'] = striplist(textGeneralName.get_text().split(','))


		#remote configuration
		textGeneralName = self.wTree.get_widget('checkRemoteUse')
		self.config['remote']['use_remote'] = textGeneralName.get_active()


		textGeneralName = self.wTree.get_widget('spinRemoteSleep')
		self.config['remote']['sleep'] = int(textGeneralName.get_value())
		#textGeneralName.set_value(-1)

		textGeneralName = self.wTree.get_widget('textRemoteHostname')
		self.config['remote']['hostname'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('textRemotePath')
		self.config['remote']['path'] = textGeneralName.get_text()
		self.config.write()






class PersyGtk():
	'''the gtk main loop and the status icon'''

	def __init__(self):
		self.statusIcon = None
		self.core = None


	def init(self, core, config, log, start=False):
		self.core = core
		self.config = config
		self.log = log

		self.log.info("Starting persy gtk")
		self.log.info("watching over: %s"%config['local']['watched'])

		menu = gtk.Menu()

		actions = []
		actions.append(('check', start, _("start/stop Persy"), self.persy_toggle))
		actions.append(('image', gtk.STOCK_EXECUTE, _('sync Remote'), self.persy_sync_remote))
		actions.append(('check', self.config['remote']['use_remote'], _("auto sync Remote"), self.persy_sync_toggle))
		#if self.config['general']['prefgitbrowser'] != "":
		#	actions.append(('image', gtk.STOCK_EXECUTE, _("start %s")%config['general']['prefgitbrowser'], self.browse))
		#dont need it!
		#actions.append(('image', gtk.STOCK_EXECUTE, _('optimize'), self.optimize))
		#actions.append(('image', gtk.STOCK_HELP, _('show Log'), self.showlog))
		#actions.append(('image', gtk.STOCK_HELP, _('show git Log'), self.showgitlog))
		actions.append(('image', gtk.STOCK_ABOUT, _('settings'), self.open_menu))
		actions.append(('image', gtk.STOCK_ABOUT, _('about'), self.about))
		actions.append(('image', gtk.STOCK_QUIT, _('quit'), self.quit_cb))



		for action in actions:
			menuItem = None
			if action[0] == 'image':
				menuItem = gtk.ImageMenuItem(action[1])
				menuItem.get_children()[0].set_label(action[2])
			else: #check
				menuItem = gtk.CheckMenuItem(action[2])
				menuItem.set_active(action[1])
			menuItem.connect('activate', action[3])
			menu.append(menuItem)

		self.statusIcon = gtk.StatusIcon()
		self.log.setStatusIcon(self.statusIcon)
		self.statusIcon.set_from_file(self.config.getAttribute('ICON_IDLE'))
		if self.config['local']['watched']:
			watched = _('watching over:')+' \n'
			for x in self.config['local']['watched']:
				watched += "- " + x + '\n'
			watched = watched[:-1]
			self.statusIcon.set_tooltip(watched)
		else:
			thewarning = _("watching no directories! You should add some directories over the command line (gui will follow)")
			self.log.warn(thewarning)
			self.statusIcon.set_tooltip(thewarning)
		self.statusIcon.connect('popup-menu', self.popup_menu_cb, menu)
		self.statusIcon.set_visible(True)

		
		if start:
			self.persy_start()
		try:
			gtk.main()
		except KeyboardInterrupt:
			self.persy_sync_remote(None) 
			self.persy_stop()
			self.log.info("bye!", verbose=True)
			sys.exit(0)
		except Exception as e:
			self.log.critical(str(e), verbose=True)

	def quit_cb(self, widget, data = None):
		'''stopts persy'''
		self.core.setonetimesync()
		self.core.persy_stop()
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

		#retrieving the installed version of persy
		VERSION=_("undefined")
		try:
			p = PersyHelper()
			VERSION=p.getSoftwareVersion('persy')
			if not VERSION:
				VERSION=_("undefined")
		except Exception as e:
			pass
		dlg.set_version(VERSION)
		dlg.set_program_name("Persy")
		dlg.set_comments(_("personal sync"))
		try:
			dlg.set_license(open(self.config.getAttribute('LICENSE_FILE')).read())
		except Exception as e:
			dlg.set_license(_("Sorry, i have a problem finding/reading the licence"))
			self.log.warn(str(e))

		dlg.set_authors([
			"Dennis Schwertel <s@digitalkultur.net>"
		])
		dlg.set_icon_from_file(self.config.getAttribute('LOGO'))
		dlg.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('LOGO'), 128, 128))
		def close(w, res):
			if res == gtk.RESPONSE_CANCEL:
				w.hide()
		dlg.connect("response", close)
		dlg.show()

	def showgitlog(self, widget, data = None):
		'''displays the git log'''
		self.showlog(widget, data, self.config.getAttribute('LOGFILE_GIT'))

	def showlog(self, widget, data = None, filename=None):
		'''displays the default.log'''
		'''executes git-gc'''
		self.log.debug('show log')
		class Starter(Thread):
			def __init__(self, log, config):
				Thread.__init__(self)
				self.log = log
				self.config = config
			def run(self):
				try:
					callcmd = []
					callcmd.append(self.config.getAttribute('XTERM'))
					callcmd.append('-e')
					callcmd.append('tail')
					callcmd.append('-n')
					callcmd.append('100')
					callcmd.append('-f')
	
					if filename:
						callcmd.append(filename)
					else:
						callcmd.append(self.config.getAttribute('LOGFILE'))

					(stdoutdata, stderrdata) = subprocess.Popen(callcmd, stdout=subprocess.PIPE).communicate()
				except Exception as e:
					self.log.warn(str(e), verbose=True)

		try:
			Starter(self.log, self.config).start()
		except Exception as e:
			self.log.warn(str(e), verbose=True)



	def persy_toggle(self, widget, data = None):
		'''toggles the state of persy (start/stop)'''
		if widget.active:
			self.persy_start()
		else:
			self.persy_stop()

	def persy_sync_remote(self, widget, data = None):
		self.log.info("onetimesync")
		self.core.setonetimesync()

	def persy_sync_toggle(self, widget, data = None):
		'''toggles the sync state (use_remote) of persy (True/False) '''
		if widget.active:
			self.config['remote']['use_remote'] = True
		else:
			self.config['remote']['use_remote'] = False
		self.config.write()

	def optimize(self, widget, data = None):
		'''calls the optimize function'''
		self.core.optimize()

	def browse(self, widget, data = None):
		self.core.browse()

	def persy_start(self):
		self.core.persy_start()

	def persy_stop(self):
		self.core.persy_stop()

	def open_menu(self, widget, data = None):
		menu = PersyGtkMenu(self.config, self.log, self)

	def syncWithRemote(self, widget, data = None):
		self.core.syncWithRemote()

	def initLocal(self, widget, data = None):
		self.core.initLocal()

	def initRemote(self, widget, data = None):
		self.core.initRemote()




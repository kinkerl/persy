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
		if not self.config['local']['watched']:
			self.log.warn("watching no directories")

		menu = gtk.Menu()

		actions = []
		actions.append(('check', start, _("start/stop Persy"), self.persy_toggle))
		actions.append(('image', gtk.STOCK_EXECUTE, _('sync Remote'), self.persy_sync_remote))
		actions.append(('check', self.config['remote']['use_remote'], _("auto sync Remote"), self.persy_sync_toggle))
		if self.config['general']['prefgitbrowser'] != "":
			actions.append(('image', gtk.STOCK_EXECUTE, _("start %s")%config['general']['prefgitbrowser'], self.browse))
		#dont need it!
		#actions.append(('image', gtk.STOCK_EXECUTE, _('optimize'), self.optimize))
		actions.append(('image', gtk.STOCK_HELP, _('show Log'), self.showlog))
		actions.append(('image', gtk.STOCK_HELP, _('show git Log'), self.showgitlog))
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
		watched = _('watching over:')+' \n'
		for x in self.config['local']['watched']:
			watched += "- " + x + '\n'
		watched = watched[:-1]
		self.statusIcon.set_tooltip(watched)
		self.statusIcon.connect('popup-menu', self.popup_menu_cb, menu)
		self.statusIcon.set_visible(True)

		
		if start:
			self.persy_start()
		try:
			gtk.main()
		except KeyboardInterrupt:
			self.log.info("bye!", verbose=True)
			sys.exit(0)
		except Exception as e:
			self.log.critical(str(e), verbose=True)

	def quit_cb(self, widget, data = None):
		'''stopts persy'''
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
		

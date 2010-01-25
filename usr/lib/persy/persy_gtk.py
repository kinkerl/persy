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
	from persy_ssh import PersySSH
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
__copyright__ = "Copyright (C) 2010 Dennis Schwertel"



class PersyGtkMenu():
	def __init__(self, config, log, gtkcore):

		#used do distinguish hboxes for watched entries
		self.hboxcounter = 0;

		self.config = config
		self.log = log
		self.gtkcore = gtkcore
		self.helper = PersyHelper()


		self.wTree = gtk.glade.XML(self.config.getAttribute('GLADEFILE'), 'window1')
		self.wTree.get_widget("window1").set_icon_from_file(self.config.getAttribute('LOGO'))
		self.wTree.get_widget("window1").set_title(_("persy settings"))

		self.wTree.get_widget("buttonSave").connect("clicked", self.save)
		self.wTree.get_widget("buttonSave").set_label(_("save"))


		textGeneralName = self.wTree.get_widget('labelGeneral')
		textGeneralName.set_label(_("general"))

		textGeneralName = self.wTree.get_widget('labelLocal')
		textGeneralName.set_label(_("backup"))

		textGeneralName = self.wTree.get_widget('labelRemote')
		textGeneralName.set_label(_("synchronization"))

		textGeneralName = self.wTree.get_widget('labelDevel')
		textGeneralName.set_label(_("administration"))

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

		textGeneralName = self.wTree.get_widget('checkGeneralFortune')
		textGeneralName.set_active(config['general']['fortune'])
		textGeneralName.set_tooltip_text(_("use fortune messages in the git commit message. disabled is fine."))
		textGeneralName.set_label(_("use fortune messages in the git commit"))

		textGeneralName = self.wTree.get_widget('labelGeneralGitBrowser')
		textGeneralName.set_label(_("default git browser"))

		textGeneralName = self.wTree.get_widget('comboboxGeneralGitBrowser')

		for browser in self.config.getAttribute('GITGUI'):
			version = self.helper.getSoftwareVersion(browser)
			if version:
				textGeneralName.insert_text(0,browser)
				if self.config['general']['prefgitbrowser'] == browser:
					textGeneralName.set_active(0)
		textGeneralName.set_tooltip_text(_("the prefered git browser for browsing the local persy repository"))

		#local configuration
		textGeneralName = self.wTree.get_widget('labelLocalSleep')
		textGeneralName.set_label(_("time to wait after an action for a backup (in seconds)"))

		textGeneralName = self.wTree.get_widget('spinLocalSleep')
		textGeneralName.set_value(int(config['local']['sleep']))
		textGeneralName.set_tooltip_text(_("time to wait after an action for a backup (in seconds)"))


		textGeneralName = self.wTree.get_widget('labelLocalWatched')
		textGeneralName.set_label('<b>'+_("list of folders persy is watching")+'</b>')


		for watched in config['local']['watched']:
			self.addWatchedEntry(None, watched)

		button = self.wTree.get_widget('buttonAddWatchedEntry')
		button.connect("clicked", self.addWatchedEntry, '')

		textGeneralName = self.wTree.get_widget('labelLocalFilesize')
		textGeneralName.set_label(_("maximal allowed size of files (in bytes)"))

		textGeneralName = self.wTree.get_widget('spinLocalFilesize')
		textGeneralName.set_value(int(config['local']['maxfilesize']))
		textGeneralName.set_tooltip_text(_("all files larger than this value will be ignored"))


		textGeneralName = self.wTree.get_widget('labelLocalExclude')
		textGeneralName.set_label(_("exclude all files matching these regular expressions"))

		textGeneralName = self.wTree.get_widget('textLocalExclude')
		textGeneralName.set_text(", ".join(config['local']['exclude']))
		textGeneralName.set_tooltip_text(_("the expressions are seperated by a comma"))

		#remote configuration

		textGeneralName = self.wTree.get_widget('checkRemoteUse')
		textGeneralName.set_active(config['remote']['use_remote'])
		textGeneralName.set_tooltip_text(_("synchronize to the remote server"))

		textGeneralName = self.wTree.get_widget('labelRemoteSleep')
		textGeneralName.set_label(_("time to wait for a synchronization (in seconds)"))

		textGeneralName = self.wTree.get_widget('spinRemoteSleep')
		textGeneralName.set_value(int(config['remote']['sleep']))
		textGeneralName.set_tooltip_text(_("interval in seconds in which a synchronization with the remote host occurs"))


		textGeneralName = self.wTree.get_widget('labelRemoteHostname')
		textGeneralName.set_label(_("hostname"))

		textGeneralName = self.wTree.get_widget('textRemoteHostname')
		textGeneralName.set_text(config['remote']['hostname'])
		textGeneralName.set_tooltip_text(_("the hostname of the remote server"))

		textGeneralName = self.wTree.get_widget('labelRemotePath')
		textGeneralName.set_label(_("repository path on the server"))

		textGeneralName = self.wTree.get_widget('textRemotePath')
		textGeneralName.set_text(config['remote']['path'])
		textGeneralName.set_tooltip_text(_("the path to the git repository on the remote server"))

		textGeneralName = self.wTree.get_widget('checkAutoshare')
		textGeneralName.set_active(config['remote']['autoshare'])
		textGeneralName.set_tooltip_text(_("if this is checked, all the computer in a sync will share the configuration file"))


		#remote actions
		thewidget = self.wTree.get_widget("testLocalSSHKey")
		thewidget.connect("clicked", self.actionTestLocalSSHKey)
		thewidget.set_label(_("test"))
		thewidget.set_tooltip_text(_('show git log'))

		thewidget = self.wTree.get_widget("testServerConnection")
		thewidget.connect("clicked", self.actionTestSSHAuth)
		thewidget.set_label(_("test"))
		thewidget.set_tooltip_text(_('show git log'))


		thewidget = self.wTree.get_widget("testRemoteRepository")
		thewidget.connect("clicked", self.actionTestRemoteServer)
		thewidget.set_label(_("test"))
		thewidget.set_tooltip_text(_('show git log'))



		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_IDLE'), 24, 24)
		textGeneralName = self.wTree.get_widget('imageLocalSSHKey')
		textGeneralName.set_from_pixbuf(pixbuf)

		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_IDLE'), 24, 24)
		textGeneralName = self.wTree.get_widget('imageServerConnection')
		textGeneralName.set_from_pixbuf(pixbuf)

		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_IDLE'), 24, 24)
		textGeneralName = self.wTree.get_widget('imageRemoteRepository')
		textGeneralName.set_from_pixbuf(pixbuf)



		#devel
		textGeneralName = self.wTree.get_widget('labelGitBrowser')
		textGeneralName.set_label(_("start a git browser"))
		thewidget = self.wTree.get_widget("buttonBrowse")
		thewidget.connect("clicked", self.gtkcore.browse)
		thewidget.set_label(_("start"))
		thewidget.set_tooltip_text(_("starts %s")%config['general']['prefgitbrowser'])

		textGeneralName = self.wTree.get_widget('labelShowLog')
		textGeneralName.set_label(_("show log"))
		thewidget = self.wTree.get_widget("buttonLog")
		thewidget.connect("clicked", self.gtkcore.showlog)
		thewidget.set_label(_("show"))
		thewidget.set_tooltip_text(_('show log'))

		textGeneralName = self.wTree.get_widget('labelShowGitLog')
		textGeneralName.set_label(_("show git log"))
		thewidget = self.wTree.get_widget("buttonGitLog")
		thewidget.connect("clicked", self.gtkcore.showgitlog)
		thewidget.set_label(_("show"))
		thewidget.set_tooltip_text(_('show git log'))

		textGeneralName = self.wTree.get_widget('labelRemoteRepository')
		textGeneralName.set_label(_("test remote repository (beware)"))
		thewidget = self.wTree.get_widget("buttonInitRemote")
		thewidget.connect("clicked", self.gtkcore.initRemote)
		thewidget.set_label(_("initialize"))
		thewidget.set_tooltip_text(_('run a initialization of the remote host'))

		textGeneralName = self.wTree.get_widget('labelSyncRemote')
		textGeneralName.set_label(_("new initial sync with remote (beware)"))
		thewidget = self.wTree.get_widget("buttonSyncRemote")
		thewidget.connect("clicked", self.gtkcore.syncWithRemote)
		thewidget.set_label(_("synchronize"))
		thewidget.set_tooltip_text(_('run a new initial synchronization with the remote host'))

		
		
	def save(self, widget, data=None):
		self.log.info("saving configuration")
		#general configuration
		textGeneralName = self.wTree.get_widget('textGeneralName')
		self.config['general']['name'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('textGeneralMail')
		self.config['general']['mail'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('checkGeneralFortune')
		self.config['general']['fortune'] = textGeneralName.get_active()

		textGeneralName = self.wTree.get_widget('comboboxGeneralGitBrowser')
		self.config['general']['prefgitbrowser'] = textGeneralName.get_active_text()

		#local configuration
		textGeneralName = self.wTree.get_widget('spinLocalSleep')
		self.config['local']['sleep'] = int(textGeneralName.get_value())


		root = self.wTree.get_widget('vbox4')
		tmparray = []
		for entry in root:
			for child in entry:
				if child.get_name().startswith('text_'):
					tmparray.append(child.get_text())
		self.config['local']['watched'] = tmparray


		
		textGeneralName = self.wTree.get_widget('spinLocalFilesize')
		self.config['local']['maxfilesize'] = int(textGeneralName.get_value())

		textGeneralName = self.wTree.get_widget('textLocalExclude')
		self.config['local']['exclude'] = self.helper.striplist(textGeneralName.get_text().split(','))

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

		textGeneralName = self.wTree.get_widget('checkAutoshare')
		self.config['remote']['autoshare'] = textGeneralName.get_active()

		#write the configuration
		self.config.write()

	def addWatchedEntry(self, widget, watched):
		root = self.wTree.get_widget('vbox4')

		hbox = gtk.HBox()
		hbox.set_name("hbox_%i"%self.hboxcounter)
		
		textLabel = gtk.Entry()
		textLabel.set_text(watched)
		textLabel.set_name("text_"+watched)
		textLabel.show()
		hbox.add(textLabel)


		button = gtk.Button('choose')
		button.connect("clicked", self.launchFileChooser, watched)
		button.set_label(_('choose'))
		button.show()
		hbox.pack_start(button, False, False)
		#hbox.add(button)

		
		button = gtk.Button('-')
		button.connect("clicked", self.removeWatchedEntry, self.hboxcounter)
		button.set_label(_(' - '))
		button.show()
		hbox.pack_start(button, False, False)
		#hbox.add(button)
		
		hbox.show()
		root.add(hbox)
		self.hboxcounter += 1


	def removeWatchedEntry(self, widget, data = None):
		for child in widget.get_parent().get_parent().get_children():
			if child.get_name() == "hbox_%i"%data:
				child.destroy()
		
		#resize the window to the minimal size
		self.wTree.get_widget("window1").resize(1, 1)


	def launchFileChooser(self, widget, data = None):
		filechooser =  gtk.FileChooserDialog(title=None	,action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		response = filechooser.run()
		try:
			if response == gtk.RESPONSE_OK:
				filename = filechooser.get_filename()
				#remove the userhome from the path
				if filename.startswith(self.config.getAttribute('USERHOME')):
					filename = filename[len(self.config.getAttribute('USERHOME'))+1:]
			
				for child in widget.get_parent().get_children():
					if child.get_name() == 'text_'+data:
						child.set_text(filename)
		except Exception as e:
			pass
		finally:
			filechooser.destroy()
			


	def actionTestRemoteServer(self, widget, data= None):
		persyssh = PersySSH(self.config, self.log)
		if persyssh.checkRemoteServer():
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_OK'), 24, 24)
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_ERROR'), 24, 24)

		textGeneralName = self.wTree.get_widget('imageRemoteRepository')
		textGeneralName.set_from_pixbuf(pixbuf)

	def actionTestSSHAuth(self, widget, data= None):
		persyssh = PersySSH(self.config, self.log)
		if persyssh.checkSSHAuth():
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_OK'), 24, 24)
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_ERROR'), 24, 24)

		textGeneralName = self.wTree.get_widget('imageServerConnection')
		textGeneralName.set_from_pixbuf(pixbuf)

	def actionTestLocalSSHKey(self, widget, data= None):
		persyssh = PersySSH(self.config, self.log)
		if persyssh.localSSHKeysExist():
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_OK'), 24, 24)
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_ERROR'), 24, 24)

		textGeneralName = self.wTree.get_widget('imageLocalSSHKey')
		textGeneralName.set_from_pixbuf(pixbuf)


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
		actions.append(('image', gtk.STOCK_HELP, _('help'), self.help))
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
			thewarning = _("watching no directories or files! You should add some in the settings menu (local -> watched)")
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

	def help(self, widget, data = None):
		import webbrowser
		webbrowser.open(self.config.getAttribute('HTMLDOCFILE'))

	def syncWithRemote(self, widget, data = None):
		self.core.syncWithRemote()

	def initLocal(self, widget, data = None):
		self.core.initLocal()

	def initRemote(self, widget, data = None):
		self.core.initRemote()




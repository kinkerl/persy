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
	from threading import Thread
	from persy_helper import PersyHelper
	from persy_helper import autorun
	from persy_ssh import PersySSH
	import subprocess
	import gtk.glade
	import pygtk
	import webbrowser
	import os
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
	"""
	This class creates the settings menu.
	It uses glade to create the interface with the corresponding persy.glade file.
	"""
	def __init__(self, config, log, gtkcore):
	
		"""
		 *   builds the settings menu
		 *   does the localization of the gui
		 *   connects all buttons to the used actions
		"""

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

		textGeneralName = self.wTree.get_widget('labelCategoryPersonal')
		textGeneralName.set_label('<b>'+_("personal information")+'</b>')

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

		textGeneralName = self.wTree.get_widget('labelCategoryAdvanced')
		textGeneralName.set_label('<b>'+_("advanced")+'</b>')

		a = autorun()
		textGeneralName = self.wTree.get_widget('checkGeneralAutostart')
		textGeneralName.set_active(a.exists('persy'))
		textGeneralName.set_label(_("start persy on login"))


		textGeneralName = self.wTree.get_widget('checkGeneralFortune')
		textGeneralName.set_active(config['general']['fortune'])
		textGeneralName.set_label(_("use fortune messages in the git commit"))
		
		if self.helper.which(config.getAttribute('FORTUNE')):
			textGeneralName.set_sensitive(True)
		else:
			textGeneralName.set_sensitive(False)
		
		textGeneralName = self.wTree.get_widget('checkGeneralAutoshare')
		textGeneralName.set_active(config['general']['autoshare'])
		textGeneralName.set_tooltip_text(_("if this is checked, all the computers in a sync will share the configuration file"))
		textGeneralName.set_label(_("share the configuration file") + _('(experimental)'))
		textGeneralName.set_sensitive(config['remote']['use_remote'])

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
		textGeneralName = self.wTree.get_widget('labelLocalWatched')
		textGeneralName.set_label('<b>'+_("list of folders persy is watching")+'</b>')

		for watched in config['local']['watched']:
			self.addWatchedEntry(None, watched)

		button = self.wTree.get_widget('buttonAddWatchedEntry')
		button.connect("clicked", self.addWatchedEntry, '')

		textGeneralName = self.wTree.get_widget('labelCategorySyncOptions')
		textGeneralName.set_label('<b>'+_("backup options")+'</b>')

		textGeneralName = self.wTree.get_widget('labelLocalSleep')
		textGeneralName.set_label(_("time to wait after an action for a backup (in seconds)"))

		textGeneralName = self.wTree.get_widget('spinLocalSleep')
		textGeneralName.set_value(int(config['local']['sleep']))
		textGeneralName.set_tooltip_text(_("time to wait after an action for a backup (in seconds)"))


		textGeneralName = self.wTree.get_widget('labelCategoryExclude')
		textGeneralName.set_label('<b>'+_("exclude options")+'</b>')

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

		textGeneralName = self.wTree.get_widget('labelCategoryExclude1')
		textGeneralName.set_label('<b>'+_("excluded submodules / directories")+'</b>')

		textGeneralName = self.wTree.get_widget('label1')
		textGeneralName.set_text("these directories are submodules and can not be tracked with persy:")


		textGeneralName = self.wTree.get_widget('label2')
		submodules = self.gtkcore.get_submodules()
		if submodules:
			textGeneralName.set_text("\n".join(submodules))
		else:
			textGeneralName.set_text("none!")

		#remote configuration
		textGeneralName = self.wTree.get_widget('labelCategoryOptions')
		textGeneralName.set_label('<b>'+_("options")+'</b>')

		textGeneralName = self.wTree.get_widget('checkRemoteUse')
		textGeneralName.set_active(config['remote']['use_remote'])
		textGeneralName.set_tooltip_text(_("synchronize to the remote server"))
		textGeneralName.connect("clicked", self.toggle_sensitive, "checkGeneralAutoshare")

		textGeneralName = self.wTree.get_widget('labelRemoteSleep')
		textGeneralName.set_label(_("time to wait for a synchronization (in seconds)"))

		textGeneralName = self.wTree.get_widget('spinRemoteSleep')
		textGeneralName.set_value(int(config['remote']['sleep']))
		textGeneralName.set_tooltip_text(_("interval in seconds in which a synchronization with the remote host occurs"))

		textGeneralName = self.wTree.get_widget('labelCategoryServerConf')
		textGeneralName.set_label('<b>'+_("server configuration")+'</b>')

		textGeneralName = self.wTree.get_widget('labelRemoteHostname')
		textGeneralName.set_label(_("hostname"))

		textGeneralName = self.wTree.get_widget('textRemoteHostname')
		textGeneralName.set_text(config['remote']['hostname'])
		textGeneralName.set_tooltip_text(_("the hostname of the remote server"))
		
		textGeneralName = self.wTree.get_widget('spinRemotePort')
		textGeneralName.set_value(int(config['remote']['port']))
		textGeneralName.set_tooltip_text(_("the port of the remote server"))

		textGeneralName = self.wTree.get_widget('labelRemoteUsername')
		textGeneralName.set_label(_("username"))
		textGeneralName.set_tooltip_text(_("the username for the remote server"))

		textGeneralName = self.wTree.get_widget('textRemoteUsername')
		textGeneralName.set_text(config['remote']['username'])
		textGeneralName.set_tooltip_text(_("the username for the remote server"))

		textGeneralName = self.wTree.get_widget('labelRemotePath')
		textGeneralName.set_label(_("repository path on the server"))

		textGeneralName = self.wTree.get_widget('textRemotePath')
		textGeneralName.set_text(config['remote']['path'])
		textGeneralName.set_tooltip_text(_("the path to the git repository on the remote server"))


		#remote actions
		textGeneralName = self.wTree.get_widget('labelCategoryActions')
		textGeneralName.set_label('<b>'+_("environment tests")+'</b>')

		textGeneralName = self.wTree.get_widget('labelTestsExplanation')
		textGeneralName.set_label(_("These are some tests to confirm if your settings are correct. If a problem occurs, the problem may be corrected if you run the corresponding action."))


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


		thewidget = self.wTree.get_widget("buttonIsInSyncWithRemote")
		thewidget.connect("clicked", self.isInSyncWithRemote)
		thewidget.set_label(_("test"))
		thewidget.set_tooltip_text(_('run a new initial synchronization with the remote host'))

		textGeneralName = self.wTree.get_widget('labelRemoteRepository')
		textGeneralName.set_label(_("test status of remote repository"))

		thewidget = self.wTree.get_widget("buttonInitRemote")
		thewidget.connect("clicked", self.init_remote)
		thewidget.set_label(_("initialize"))
		thewidget.set_tooltip_text(_('run a initialization of the remote host'))

		textGeneralName = self.wTree.get_widget('labelSyncRemote')
		textGeneralName.set_label(_("is persy in a sync pack with remote host"))

		thewidget = self.wTree.get_widget("buttonSyncRemote")
		thewidget.connect("clicked", self.sync_with_remote)
		thewidget.set_label(_("link"))
		thewidget.set_tooltip_text(_('run a new initial synchronization with the remote host'))



		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_IDLE'), 24, 24)
		textGeneralName = self.wTree.get_widget('imageLocalSSHKey')
		textGeneralName.set_from_pixbuf(pixbuf)

		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_IDLE'), 24, 24)
		textGeneralName = self.wTree.get_widget('imageServerConnection')
		textGeneralName.set_from_pixbuf(pixbuf)

		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_IDLE'), 24, 24)
		textGeneralName = self.wTree.get_widget('imageRemoteRepository')
		textGeneralName.set_from_pixbuf(pixbuf)

		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_IDLE'), 24, 24)
		textGeneralName = self.wTree.get_widget('imageIsInSyncWithRemote')
		textGeneralName.set_from_pixbuf(pixbuf)


		#devel
		textGeneralName = self.wTree.get_widget('labelCategoryMonitoring')
		textGeneralName.set_label('<b>'+_("monitoring")+'</b>')

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


	def save(self, widget, data=None):
		"""
		converts the values from the gui to PersyConfig values and executes the save function on the config object
		"""
		self.log.info("saving configuration")
		#general configuration
		textGeneralName = self.wTree.get_widget('textGeneralName')
		self.config['general']['name'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('textGeneralMail')
		self.config['general']['mail'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('checkGeneralFortune')
		self.config['general']['fortune'] = textGeneralName.get_active()

		textGeneralName = self.wTree.get_widget('checkGeneralAutostart')
		autostart = textGeneralName.get_active()
		a = autorun()
		if autostart and not a.exists('persy'):
			a.add('persy', self.config.getAttribute('PERSY_BIN') + ' --start')
		if not autostart and a.exists('persy'):
			a.remove('persy')


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
		
		textGeneralName = self.wTree.get_widget('spinRemotePort')
		self.config['remote']['port'] = int(textGeneralName.get_value())		

		textGeneralName = self.wTree.get_widget('textRemotePath')
		self.config['remote']['path'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('textRemoteUsername')
		self.config['remote']['username'] = textGeneralName.get_text()

		textGeneralName = self.wTree.get_widget('checkGeneralAutoshare')
		self.config['general']['autoshare'] = textGeneralName.get_active()

		#write the configuration
		self.config.write()

	def addWatchedEntry(self, widget, watched):
		"""
		code for adding a new entry for a watched directory to the gui
		"""
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
		"""
		removing a watched directory entry from the widget. 
		the name of the directory is stored in data
		"""
		for child in widget.get_parent().get_parent().get_children():
			if child.get_name() == "hbox_%i"%data:
				child.destroy()
		
		#resize the window to the minimal size
		self.wTree.get_widget("window1").resize(1, 1)


	def launchFileChooser(self, widget, data = None):
		"""
		launchdes a filechooser dialog for a folder
		"""
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
		"""
		persy environment test action.
		uses PersySSH to check the remote Server
		"""
		persyssh = PersySSH(self.config, self.log)
		if persyssh.checkRemoteServer():
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_OK'), 24, 24)
			thewidget = self.wTree.get_widget('imageRemoteRepository')
			thewidget.set_tooltip_text(_('all ok'))
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_ERROR'), 24, 24)
			thewidget = self.wTree.get_widget('imageRemoteRepository')
			thewidget.set_tooltip_text(_('the remote repository is not ok. maybe the path on the server is incorrect or it is not initialized. run the "initialize" action to do so'))

		textGeneralName = self.wTree.get_widget('imageRemoteRepository')
		textGeneralName.set_from_pixbuf(pixbuf)

	def actionTestSSHAuth(self, widget, data= None):
		"""
		persy environment test action.
		uses PersySSH to check the server authentification
		"""
		persyssh = PersySSH(self.config, self.log)
		if persyssh.checkSSHAuth():
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_OK'), 24, 24)
			thewidget = self.wTree.get_widget('imageServerConnection')
			thewidget.set_tooltip_text(_('all ok'))
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_ERROR'), 24, 24)
			thewidget = self.wTree.get_widget('imageServerConnection')
			thewidget.set_tooltip_text(_('the connection to the server was not possible. please check your settings above and if you have published your ssh public key to the server. if not, you can run the "publish" action'))

		textGeneralName = self.wTree.get_widget('imageServerConnection')
		textGeneralName.set_from_pixbuf(pixbuf)

	def actionTestLocalSSHKey(self, widget, data= None):
		"""
		persy environment test action.
		uses PersySSH to check if local ssh keys do exist
		"""
		persyssh = PersySSH(self.config, self.log)
		if persyssh.localSSHKeysExist():
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_OK'), 24, 24)
			thewidget = self.wTree.get_widget('imageLocalSSHKey')
			thewidget.set_tooltip_text(_('all ok'))
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_ERROR'), 24, 24)
			thewidget = self.wTree.get_widget('imageLocalSSHKey')
			thewidget.set_tooltip_text(_('no local ssh keys are present. these are important for a serverconnection. you may want to run the "create" action to create these'))

		textGeneralName = self.wTree.get_widget('imageLocalSSHKey')
		textGeneralName.set_from_pixbuf(pixbuf)

	def isInSyncWithRemote(self, widget, data= None):
		"""
		persy environment test action.
		uses gtkcore to test if persy is in sync with remote (has an git-remote entry for origin)
		"""
		if self.gtkcore.isInSyncWithRemote(widget):
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_OK'), 24, 24)
			thewidget = self.wTree.get_widget('imageIsInSyncWithRemote')
			thewidget.set_tooltip_text(_('all ok'))
		else:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('ICON_ERROR'), 24, 24)
			thewidget = self.wTree.get_widget('imageIsInSyncWithRemote')
			thewidget.set_tooltip_text(_('persy is not in sync with the remote server. you may want to run the "link" action to fix this'))

		textGeneralName = self.wTree.get_widget('imageIsInSyncWithRemote')
		textGeneralName.set_from_pixbuf(pixbuf)
		
	
	def toggle_sensitive(self, widget, data=None):
		"""
		changes sensitive from widgets
		"""
		self.wTree.get_widget(data).set_sensitive(widget.get_active())

	def sync_with_remote(self, widget, data=None):
		dia = gtk.Dialog(_('Question!'),
				 widget.get_toplevel(),  #the toplevel wgt of your app
				 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  #binary flags or'ed together
				 (_("synchronize now"), 77, gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
		label = gtk.Label(_('Do you want to synchronize now? This should only be done once at the beginning.'))
		label.show()
		dia.vbox.pack_start(label)
		dia.show()
		result = dia.run()
		if result == 77:
			self.gtkcore.syncWithRemote()
		dia.destroy()

	def init_remote(self, widget, data=None):
		dia = gtk.Dialog(_('Question!'),
				 widget.get_toplevel(),  #the toplevel wgt of your app
				 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  #binary flags or'ed together
				 (_("initialize now"), 77, gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
		label = gtk.Label(_('Do you want to initialize now? This should only be done once at the beginning.'))
		label.show()
		dia.vbox.pack_start(label)
		dia.show()
		result = dia.run()
		if result == 77:
			self.gtkcore.initRemote(widget, data)
		dia.destroy()


class PersyGtk():
	"""
	the gtk main loop and the status icon
	"""

	def __init__(self):
		self.statusIcon = None
		self.indicator = None
		self.core = None


	def init(self, core, config, log, start=False):
		"""
		creates the satus icon and appends all actions to it.
		initializes the rest of the gtk stuff and runs persy if start is True
		"""
		self.core = core
		self.config = config
		self.log = log

		self.log.info("Starting persy gtk")
		self.log.info("watching over: %s"%config['local']['watched'])
		import gtk
		menu = gtk.Menu()



		menuItem = gtk.MenuItem(_('Status: not running'))
		menuItem.set_sensitive(False)
		menuItem.connect('activate',self.showlog)
		menuItem.show()
		menu.append(menuItem)

		self.log.set_status_text(menuItem)

		menuItem = gtk.MenuItem(_("Start Persy"))
		#menuItem.set_active(start)
		menuItem.connect('activate',self.persy_toggle)
		menuItem.show()
		menu.append(menuItem)

		self.log.set_status_button(menuItem)
	

		sep = gtk.SeparatorMenuItem()
		sep.show()
		menu.append(sep)


		if self.config['local']['watched']:
			menuItem = gtk.MenuItem(_('Watched folders')+':')
			menuItem.set_sensitive(False)
			menuItem.show()
			menu.append(menuItem)

			#watched = _('watching over:')+' \n'
			for x in self.config['local']['watched']:
				menuItem = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
				menuItem.get_children()[0].set_label(x)
				menuItem.show()
				menuItem.connect('activate', self.open_folder)
				menu.append(menuItem)
	
				#watched += "- " + x + '\n'
			#watched = watched[:-1]
			#self.statusIcon.set_tooltip(watched)
		else:
			thewarning = _("Watching no directories or files!\nYou should add some in the settings menu")
			menuItem = gtk.ImageMenuItem(gtk.STOCK_DIALOG_ERROR)
			menuItem.get_children()[0].set_label(thewarning)
			menuItem.connect('activate', self.open_menu)
			menuItem.show()
			menu.append(menuItem)
			self.log.warn(thewarning)
			#self.statusIcon.set_tooltip(thewarning)

		sep = gtk.SeparatorMenuItem()
		sep.show()
		menu.append(sep)

		actions = []
		#actions.append(('check', start, _("start/stop Persy"), self.persy_toggle))
		#actions.append(('image', gtk.STOCK_EXECUTE, _('sync Remote'), self.persy_sync_remote))
		#actions.append(('check', self.config['remote']['use_remote'], _("auto sync Remote"), self.persy_sync_toggle))
		#if self.config['general']['prefgitbrowser'] != "":
		#	actions.append(('image', gtk.STOCK_EXECUTE, _("start %s")%config['general']['prefgitbrowser'], self.browse))
		#dont need it!
		#actions.append(('image', gtk.STOCK_EXECUTE, _('optimize'), self.optimize))
		#actions.append(('image', gtk.STOCK_HELP, _('show Log'), self.showlog))
		#actions.append(('image', gtk.STOCK_HELP, _('show git Log'), self.showgitlog))
		actions.append(('image', gtk.STOCK_PREFERENCES, _('Preferences'), self.open_menu))
		#actions.append(('image', gtk.STOCK_HELP, _('help'), self.help))
		actions.append(('image', gtk.STOCK_ABOUT, _('About'), self.about))
		actions.append(('image', gtk.STOCK_QUIT, _('Quit'), self.quit_cb))

		for action in actions:
			menuItem = None
			if action[0] == 'image':
				menuItem = gtk.ImageMenuItem(action[1])
				menuItem.get_children()[0].set_label(action[2])
			else: #check
				menuItem = gtk.CheckMenuItem(action[2])
				menuItem.set_active(action[1])
			menuItem.connect('activate', action[3])
			menuItem.show()
			menu.append(menuItem)





		createstatusicon = False #tmp flag to 
		if self.config['general']['create_gui_indicator']: #default is true	
			try:
				#create app indicator
				import gobject
				import appindicator
				self.indicator = appindicator.Indicator ("persy", 'persy_idle', appindicator.CATEGORY_APPLICATION_STATUS)
				self.indicator.set_status (appindicator.STATUS_ACTIVE)
				self.indicator.set_menu(menu)
				self.log.set_indicator(self.indicator)
			except Exception as e:
				createstatusicon = True

		if createstatusicon or self.config['general']['create_gui_statusicon']: #default is false
			#if app indicator was not created because of an error or the config commands to create one, create status icon
			self.statusIcon = gtk.StatusIcon()
			self.log.setStatusIcon(self.statusIcon)
			self.statusIcon.set_from_file(self.config.getAttribute('ICON_IDLE'))
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

	def quit_cb(self, unused_widget, data = None):
		"""
		start a last remote sync and then stops persy (with the use of pery_core)
		"""
		self.core.setonetimesync()
		self.core.persy_stop()
		if data:
			data.set_visible(False)
		gtk.main_quit()
		sys.exit(0)

	def popup_menu_cb(self, unused_widget, unused_button, time, data = None):
		"""
		show the rightclick menu of the status icon
		"""
		if data:
			data.show_all()
			data.popup(None, None, None, 3, time)


	def about(self, unused_widget, unused_data = None):
		"""
		create and show the about dialog
		"""
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
		dlg.set_program_name("persy")
		dlg.set_comments(_("personal synchronization"))
		try:
			dlg.set_license(open(self.config.getAttribute('LICENSE_FILE')).read())
		except Exception as e:
			dlg.set_license(_("Sorry, i have a problem finding/reading the licence"))
			self.log.warn(str(e))

		dlg.set_authors([
			"Dennis Schwertel <s@digitalkultur.net>",
			"Rafael Römhild <rafael@roemhild.de>"
		])
		dlg.set_icon_from_file(self.config.getAttribute('LOGO'))
		dlg.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(self.config.getAttribute('LOGO'), 128, 128))
		def close(w, res):
			if res == gtk.RESPONSE_CANCEL:
				w.hide()
		dlg.connect("response", close)
		dlg.show()

	def showgitlog(self, widget, data = None):
		"""
		displays the git log
		"""
		self.showlog(widget, data, self.config.getAttribute('LOGFILE_GIT'))

	def showlog(self, unused_widget, unused_data = None, filename=None):
		"""
		displays the default.log. uses xterm for display
		"""
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



	def persy_toggle(self, widget = None, unused_data = None):
		"""
		toggles the state of persy (start/stop)
		"""
		if self.core.running:
			self.persy_stop()
		else:
			self.persy_start()

	def persy_sync_remote(self, unused_widget = None, unused_data = None):
		self.log.info("onetimesync")
		self.core.setonetimesync()

	def persy_sync_toggle(self, widget = None, unused_data = None):
		"""
		toggles the sync state in the config (use_remote) of persy (True/False) 

		if the widget is active, use_remote will be true
		"""
		if widget and widget.active:
			self.config['remote']['use_remote'] = True
		else:
			self.config['remote']['use_remote'] = False
		self.config.write()

	def optimize(self, unused_widget = None, unused_data = None):
		"""
		calls the optimize function in core
		"""
		self.core.optimize()

	def browse(self, unused_widget = None, unused_data = None):
		"""
		calls the browse function in core
		"""
		self.core.browse()

	def persy_start(self):
		"""
		calls the persy_start function in core
		"""
		self.core.persy_start()

	def persy_stop(self):
		"""
		calls the persy_stop function in core
		"""
		self.core.persy_stop()

	def open_menu(self, unused_widget = None, unused_data = None):
		"""
		creates a new PersyGtkMenu instance
		"""
		PersyGtkMenu(self.config, self.log, self)

	def open_folder(self, unused_widget = None, unused_data = None):
		#this is linux only,
		#FIXME: this will have problems with absolute/relative filenames
		os.system('xdg-open "%s/%s"' % (self.config.getAttribute('USERHOME'),unused_widget.get_children()[0].get_label())) 
		#On OSX, I can open a window in the finder with
		#os.system('open "%s"' % foldername)
		#and on Windows with
		#os.startfile(foldername)


	def help(self, unused_widget = None, unused_data = None):
		"""
		opens the system-webbrowser witht the persy documentation
		 *   windows = ie
		 *   linux/unix = firefox (most of the time)
		 *   mac = safari
		"""
		webbrowser.open(self.config.getAttribute('HTMLDOCFILE'))

	def syncWithRemote(self, unused_widget = None, unused_data = None):
		"""
		calls the syncWithRemote function in core
		"""
		self.core.syncWithRemote()

	def init_local(self, unused_widget = None, unused_data = None):
		"""
		calls the init_local function in core
		"""
		self.core.init_local()

	def initRemote(self, unused_widget = None, unused_data = None):
		"""
		calls the initRemote function in core
		"""
		self.core.initRemote()

	def get_submodules(self):
		"""
		returns the result of get_submodules from core
		"""
		return self.core.git_get_submodules()

	def isInSyncWithRemote(self, unused_widget = None, unused_data = None):
		"""
		returns the result of isInSyncWithRemote from core
		"""
		return self.core.isInSyncWithRemote()




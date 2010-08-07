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
	from configobj import ConfigObj
	from persy_helper import PersyHelper
	import os
	import getpass
	import platform
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



class PersyConfig():
	"""
	Configuration class for Persy

	This class handels all the configuration and environment attributes.
	It depends on the configobj class.
	"""

	def __init__(self, configfile = None):
		"""
		the the static attributes and parses the configuration file
		"""
		self.attributes = {}
		self.p = PersyHelper()

		#host stuff
		self.attributes['DIST'] = platform.dist() # ('Ubuntu', '9.10', 'karmic')

		# files and dirs used by persy
		self.attributes['USERHOME'] = os.environ["HOME"]
		self.attributes['LOCALSSHDIR']=os.path.join(self.attributes['USERHOME'],'.ssh')
		self.attributes['PERSY_DIR'] = os.path.join(self.attributes['USERHOME'], '.persy')
		self.attributes['GIT_DIR'] = os.path.join(self.attributes['PERSY_DIR'],'git')
		self.attributes['GIT_WORK_TREE'] =self.attributes['USERHOME']
		self.attributes['GIT_LOCKFILE'] = os.path.join(self.attributes['GIT_DIR'],'index.lock')
		self.attributes['LOGFILE']=os.path.join(self.attributes['PERSY_DIR'],'default.log')
		self.attributes['LOGFILE_GIT']=os.path.join(self.attributes['PERSY_DIR'],'git.log')
		self.attributes['GITIGNOREFILE']=os.path.join(self.attributes['GIT_DIR'], 'info','exclude')
		self.attributes['EXAMPLECONFIG']='/usr/share/persy/example_config'
		self.attributes['GLADEFILE']='/usr/share/persy/lib/persy.glade'
		self.attributes['VERSIONFILE']='/usr/share/persy/assets/VERSION'
		self.attributes['HTMLDOCFILE']='/usr/share/doc/persy/index.html'
		self.attributes['PERSY_BIN']='/usr/bin/persy'

		#set the config file to default or a new one
		if configfile:
			self.attributes['CONFIGFILE']=configfile
		else:
			self.attributes['CONFIGFILE']=os.path.join(self.attributes['PERSY_DIR'],'config')

		#path to some files and icons
		self.attributes['ICON_IDLE'] = '/usr/share/persy/assets/persy.svg'
		self.attributes['ICON_OK'] = '/usr/share/persy/assets/persy_ok.svg'
		self.attributes['ICON_UNSYNCED'] = '/usr/share/persy/assets/persy_unsynced.svg'
		self.attributes['ICON_UNTRACKED'] = '/usr/share/persy/assets/persy_untracked.svg'
		self.attributes['ICON_WARN'] = '/usr/share/persy/assets/persy_warn.svg'
		self.attributes['ICON_ERROR'] = '/usr/share/persy/assets/persy_error.svg'


		#logo depends on DIST!
		if self.attributes['DIST'][0] == 'Ubuntu':
			self.attributes['LOGO'] = '/usr/share/persy/assets/persy.svg'
		elif self.attributes['DIST'][0] == 'LinuxMint':
			self.attributes['LOGO'] = '/usr/share/persy/assets/dist/persy_linuxmint.svg'
		elif self.attributes['DIST'][0] == 'fedora':
			self.attributes['LOGO'] = '/usr/share/persy/assets/dist/persy_fedora.svg'
		else:
			self.attributes['LOGO'] = '/usr/share/persy/assets/persy.svg'

		#path to the license file
		self.attributes['LICENSE_FILE'] = '/usr/share/persy/assets/GPL-2'

		#git variables used by persy
		self.attributes['SERVER_NICK']='origin'
		self.attributes['BRANCH']='master'

		#default config entries
		self.attributes['DEFAULT_LOCAL_SLEEP'] = 5
		self.attributes['DEFAULT_REMOTE_SLEEP'] = 300
		self.attributes['DEFAULT_REMOTE_HOSTNAME'] = ''
		self.attributes['DEFAULT_REMOTE_PORT'] = 22
		self.attributes['DEFAULT_REMOTE_PATH'] = ''

		try:
			#read the configuration
			self.attributes['DEFAULT_CONFIG']= open(self.attributes['EXAMPLECONFIG']).read()
			#replace the placeholder with the configuration values
			self.attributes['DEFAULT_CONFIG'] = self.attributes['DEFAULT_CONFIG'] % self.attributes
		except IOError as e:
			print str(e)

		#xterm terminal
		self.attributes['XTERM'] = "xterm"
		
		#fortune	
		self.attributes['FORTUNE'] = "fortune"

		#autoshare
		self.attributes['AUTOSHARE'] = "autoshare"

		#the default gui git browser
		self.attributes['GITGUI']=["gitk", "qgit"] #possible browsers

		if not os.path.exists(self.attributes['CONFIGFILE']):
			if not os.path.exists(self.attributes['PERSY_DIR']):
				os.mkdir(self.attributes['PERSY_DIR'])
			with open(self.attributes['CONFIGFILE'], "w+") as f:
				f.write(self.attributes['DEFAULT_CONFIG'])

		config = ConfigObj(self.attributes['CONFIGFILE'])

		#config check if everything is ok
		#================================
		#general GIT_DIR
		if not config['general'].has_key('gitdir') or not config['general']['gitdir']:
			config['general']['gitdir'] = self.attributes['GIT_DIR']

		#general GIT_WORK_TREE
		if not config['general'].has_key('gitworkdir') or not config['general']['gitworkdir']:
			config['general']['gitworktree'] = self.attributes['GIT_WORK_TREE']

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

		#general create_gui_indicator
		#flag to create an app indicator. default is True! 
		if not config['general'].has_key('create_gui_indicator'):
			config['general']['create_gui_indicator'] = True
		if type(config['general']['create_gui_indicator']) is str and config['general']['create_gui_indicator'].lower()  == 'false':
			config['general']['create_gui_indicator'] = False
		if not type(config['general']['create_gui_indicator']) is bool:
			config['general']['create_gui_indicator'] = True
		
		#general create_gui_statusicon
		#flag to create a status icon. default is False. 
		#Will still try to create a status icon if indicator fails! 
		if not config['general'].has_key('create_gui_statusicon'):
			config['general']['create_gui_statusicon'] = False
		if type(config['general']['create_gui_statusicon']) is str and config['general']['create_gui_statusicon'].lower()  == 'true':
			config['general']['create_gui_statusicon'] = True
		if not type(config['general']['create_gui_statusicon']) is bool:
			config['general']['create_gui_statusicon'] = False
		
	
	    	#general autoshare
		if not config['general'].has_key('autoshare'):
			config['general']['autoshare'] = False
		if type(config['general']['autoshare']) is str and config['general']['autoshare'].lower()  == 'true':
			config['general']['autoshare'] = True
		if not type(config['general']['autoshare']) is bool:
			config['general']['autoshare'] = False

		#general gitgui
		if not config['general'].has_key('prefgitbrowser'):
			config['general']['prefgitbrowser'] = ""
			for gitbrowser in self.attributes['GITGUI']:
				if self.p.getSoftwareVersion(gitbrowser):
					config['general']['prefgitbrowser'] = gitbrowser
					break
		if type(config['general']['prefgitbrowser']) is str:
			if config['general']['prefgitbrowser'].lower() in self.attributes['GITGUI'] and self.p.getSoftwareVersion(config['general']['prefgitbrowser']):
				config['general']['prefgitbrowser'] = config['general']['prefgitbrowser'].lower()
			else:
				config['general']['prefgitbrowser'] = ""
				for gitbrowser in self.attributes['GITGUI']:
					if self.p.getSoftwareVersion(gitbrowser):
						config['general']['prefgitbrowser'] = gitbrowser
						break
		if not type(config['general']['prefgitbrowser']) is str:
			#config is strange?! set it to the first possible prowser
			config['general']['prefgitbrowser'] = self.attributes['GITGUI'][0]


		#local sleep
		if not config['local'].has_key('sleep') or not config['local']['sleep']:
			config['local']['sleep'] = self.attributes['DEFAULT_LOCAL_SLEEP']

		if not type(config['local']['sleep']) is int:
			try:
				config['local']['sleep'] = int(config['local']['sleep'])
			except Exception as e:
				config['local']['sleep'] = self.attributes['DEFAULT_LOCAL_SLEEP']

		#local watched
		if not config['local'].has_key('watched') or not config['local']['watched']:
			config['local']['watched'] = []

		if type(config['local']['watched']) is str:
			config['local']['watched'] = [config['local']['watched']]

		if not type(config['local']['watched']) is list:
			config['local']['watched'] = []
		#remove spaces
		config['local']['watched'] = self.p.striplist(config['local']['watched'])

		#local maxfilesize
		if not config['local'].has_key('maxfilesize') or not type(config['local']['maxfilesize']) is str:
			config['local']['maxfilesize'] = 0
		if not type(config['local']['maxfilesize']) is int:
			try:
				config['local']['maxfilesize'] = int(config['local']['maxfilesize'])
			except Exception as e:
				config['local']['maxfilesize'] = 0

		#local exclude
		if not config['local'].has_key('exclude'):
			config['local']['exclude']=[]
		if type(config['local']['exclude']) is str:
			config['local']['exclude'] = [config['local']['exclude']]
		if not type(config['local']['exclude']) is list:
			config['local']['exclude'] = []
		#remove spaces
		config['local']['exclude'] = self.p.striplist(config['local']['exclude'])

		#remote use_remote
		if not config['remote'].has_key('use_remote'):
			config['remote']['use_remote'] = False
		if type(config['remote']['use_remote']) is str and config['remote']['use_remote'].lower()  == 'true':
			config['remote']['use_remote'] = True
		if not type(config['remote']['use_remote']) is bool:
			config['remote']['use_remote'] = False

		#remote sleep
		if not config['remote'].has_key('sleep') or not config['remote']['sleep']:
			config['remote']['sleep'] = self.attributes['DEFAULT_REMOTE_SLEEP']

		if not type(config['remote']['sleep']) is int:
			try:
				config['remote']['sleep'] = int(config['remote']['sleep'])
			except Exception as e:
				config['remote']['sleep'] = self.attributes['DEFAULT_REMOTE_SLEEP']

		#remote hostname
		if not config['remote'].has_key('hostname') or not type(config['remote']['hostname']) is str:
			config['remote']['hostname'] = self.attributes['DEFAULT_REMOTE_HOSTNAME']
			
		#remote port
		if not config['remote'].has_key('port') or not config['remote']['port']:
			config['remote']['port'] = self.attributes['DEFAULT_REMOTE_PORT']

		#remote username
		if not config['remote'].has_key('username') or not type(config['remote']['username']) is str:
			config['remote']['username'] = getpass.getuser() #if not set, use the current

		#remote path
		if not config['remote'].has_key('path') or not type(config['remote']['path']) is str:
			config['remote']['path'] = self.attributes['DEFAULT_REMOTE_PATH']


		#use gitsvn
		if not config['remote'].has_key('use_gitsvn'):
			config['remote']['use_gitsvn'] = False
		if type(config['remote']['use_gitsvn']) is str and config['remote']['use_gitsvn'].lower()  == 'true':
			config['remote']['use_gitsvn'] = True
		if not type(config['remote']['use_gitsvn']) is bool:
			config['remote']['use_gitsvn'] = False


		self.config = config


	def write(self):
		"""
		uses confobj to write the configuration
		"""
		self.config.write()


	def getAttribute(self, key):
		"""
		key -- the name of the attribute
		
		returns the value to a key
		"""
		return self.attributes[key]


	def has_key(self, item):
		"""
		item -- name of item in the config
		
		check if this config object has the key
		"""
		return self.config.has_key(item)


	def __getitem__(self, item):
		"""
		item -- name of the item in the config
		
		allows compartibility with configobj for config[item] like querys
		"""
		return self.config[item]


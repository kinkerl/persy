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
	from configobj import ConfigObj
	from persy_helper import PersyHelper
	import os
except ImportError as e:
	print _("You do not have all the dependencies:")
	print str(e)
	sys.exit(1)
except Exception as e:
	print _("An error occured when initialising one of the dependencies!")
	print str(e)
	sys.exit(1)




class PersyConfig():
	'''Handles the configuration for Persy'''


	def __init__(self):

		self.attributes = {}

		# files and dirs used by persy
		self.attributes['USERHOME'] = os.environ["HOME"]
		self.attributes['PERSY_DIR'] = os.path.join(self.attributes['USERHOME'], '.persy')
		self.attributes['GIT_DIR'] = os.path.join(self.attributes['PERSY_DIR'],'git')
		self.attributes['GIT_LOCKFILE'] = os.path.join(self.attributes['GIT_DIR'],'index.lock')
		self.attributes['LOGFILE']=os.path.join(self.attributes['PERSY_DIR'],'default.log')
		self.attributes['LOGFILE_GIT']=os.path.join(self.attributes['PERSY_DIR'],'git.log')
		self.attributes['GITIGNOREFILE']=os.path.join(self.attributes['GIT_DIR'], 'info','exclude')
		self.attributes['CONFIGFILE']=os.path.join(self.attributes['PERSY_DIR'],'config')
		self.attributes['EXAMPLECONFIG']='/usr/lib/persy/example_config'

		#path to some files and icons
		self.attributes['ICON_IDLE'] = '/usr/lib/persy/persy.svg'
		self.attributes['ICON_OK'] = '/usr/lib/persy/persy_ok.svg'
		self.attributes['ICON_UNSYNCED'] = '/usr/lib/persy/persy_unsynced.svg'
		self.attributes['ICON_UNTRACKED'] = '/usr/lib/persy/persy_untracked.svg'
		self.attributes['ICON_WARN'] = '/usr/lib/persy/persy_warn.svg'
		self.attributes['ICON_ERROR'] = '/usr/lib/persy/persy_error.svg'
		self.attributes['LOGO'] = '/usr/lib/persy/persy.svg'

		#path to the license file
		self.attributes['LICENSE_FILE'] = '/usr/share/common-licenses/GPL-2'

		#git variables used by persy
		self.attributes['SERVER_NICK']='origin'
		self.attributes['BRANCH']='master'




		#default config entries
		self.attributes['DEFAULT_LOCAL_SLEEP'] = 5
		self.attributes['DEFAULT_REMOTE_SLEEP'] = 300
		self.attributes['DEFAULT_REMOTE_HOSTNAME'] = ''
		self.attributes['DEFAULT_REMOTE_PATH'] = ''

		try:
			self.attributes['DEFAULT_CONFIG']= open(self.attributes['EXAMPLECONFIG']).read()%(self.attributes['DEFAULT_LOCAL_SLEEP'], self.attributes['DEFAULT_REMOTE_SLEEP'], self.attributes['DEFAULT_REMOTE_HOSTNAME'], self.attributes['DEFAULT_REMOTE_PATH'])
		except IOError as e:
			print str(e)






		#xterm terminal
		self.attributes['XTERM'] = "xterm"
		#fortune	
		self.attributes['FORTUNE'] = "fortune"

		#the default gui git browser
		self.attributes['GITGUI']=["gitk", "qgit"] #possible browsers
		self.p = PersyHelper()

		if not os.path.exists(self.attributes['CONFIGFILE']):
			with open(self.attributes['CONFIGFILE'], "w+") as f:
				f.write(self.attributes['DEFAULT_CONFIG'])

		config = ConfigObj(self.attributes['CONFIGFILE'])

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
			if getSoftwareVersion(self.GITGUI[0]):
				config['general']['prefgitbrowser'] = self.attributes['GITGUI'][0]
			elif getSoftwareVersion(self.GITGUI[1]):
				config['general']['prefgitbrowser'] = self.attributes['GITGUI'][1]
			else:
				#log.critical(_("gitk and qgit is not installed, this should not happen!"))
				config['general']['prefgitbrowser'] = ""
		if type(config['general']['prefgitbrowser']) is str:
			if config['general']['prefgitbrowser'].lower() in self.attributes['GITGUI'] and self.p.getSoftwareVersion(config['general']['prefgitbrowser']):
				config['general']['prefgitbrowser'] = config['general']['prefgitbrowser'].lower()
			else:
				if self.p.getSoftwareVersion(self.attributes['GITGUI'][0]):
					config['general']['prefgitbrowser'] = self.attributes['GITGUI'][0]
				elif self.p.getSoftwareVersion(self.GITGUI[1]):
					config['general']['prefgitbrowser'] = self.attributes['GITGUI'][1]
				else:
					#log.warn(_("gitk and qgit is not installed, this should not happen!"))
					config['general']['prefgitbrowser'] = ""
		if not type(config['general']['prefgitbrowser']) is str:
			#log.warn(_("the config for the prefered git browser is broken?"))
			config['general']['prefgitbrowser'] = ""


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
			config['remote']['sleep'] = self.attributes['DEFAULT_REMOTE_SLEEP']

		if not type(config['remote']['sleep']) is int:
			try:
				config['remote']['sleep'] = int(config['remote']['sleep'])
			except Exception as e:
				config['remote']['sleep'] = self.attributes['DEFAULT_REMOTE_SLEEP']

		#remote hostname
		if not config['remote'].has_key('hostname') or not type(config['remote']['hostname']) is str:
			config['remote']['hostname'] = self.attributes['DEFAULT_REMOTE_HOSTNAME']

		#remote path
		if not config['remote'].has_key('path') or not type(config['remote']['path']) is str:
			config['remote']['path'] = self.attributes['DEFAULT_REMOTE_PATH']

		self.config = config

	def __getitem__(self, item):
		return self.config[item]

	def write(self):
		self.config.write()

	def getAttribute(self, key):
		return self.attributes[key]
	def getConfig(self):
		return self.config

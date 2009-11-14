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



class PersyConfig():
	'''Handles the configuration for Persy'''

	def __init__(self, configfile):
		#the default gui git browser
		self.GITGUI=["gitk", "qgit"] #possible browsers
		self.p = PersyHelper()

		if not os.path.exists(configfile):
			with open(configfile, "w+") as f:
				f.write(DEFAULT_CONFIG)

		config = ConfigObj(configfile)

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
				config['general']['prefgitbrowser'] = self.GITGUI[0]
			elif getSoftwareVersion(self.GITGUI[1]):
				config['general']['prefgitbrowser'] = self.GITGUI[1]
			else:
				log.critical(_("gitk and qgit is not installed, this should not happen!"))
				config['general']['prefgitbrowser'] = ""
		if type(config['general']['prefgitbrowser']) is str:
			if config['general']['prefgitbrowser'].lower() in self.GITGUI and self.p.getSoftwareVersion(config['general']['prefgitbrowser']):
				config['general']['prefgitbrowser'] = config['general']['prefgitbrowser'].lower()
			else:
				if self.p.getSoftwareVersion(self.GITGUI[0]):
					config['general']['prefgitbrowser'] = self.GITGUI[0]
				elif self.p.getSoftwareVersion(self.GITGUI[1]):
					config['general']['prefgitbrowser'] = self.GITGUI[1]
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

		self.config = config

	def getConfig(self):
		return self.config

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
	LOCALEDIR = '/usr/lib/persy/locale'
	#init the localisation
	gettext.install("messages", LOCALEDIR)
except Exception as e:
	print "I have problems initializing the translations (gettext). \
Will use plain english instead"
	print str(e)

	#check if the _ function is initialized, if not, do a fallback!
	if not _:
		def _(msg):
			"""fallback-function if the original function 
			did not initialize propperly"""
			return msg


try:
	import sys
	from persy_config import PersyConfig
	from persy_core import Core
	from persy_gtk import PersyGtk
	from persy_helper import PersyHelper
	from persy_talker import Talker
	import os
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




def main(argv):
	"""
	the main function. the command line arguments are processed here and the next actions are started here too
	"""
	args = argv[1:]

	#cli options
	from optparse import OptionParser
	parser = OptionParser(usage = _("use --start to start the daemon"))
	parser.add_option("--start", action="store_true", default=False, help=_("starts persy"))
	parser.add_option("--initremote", action="store_true", default=False, help=_("initializes the remote repository"))
	parser.add_option("--syncwithremote", action="store_true", default=False, help=_("syncs with a remote repository"))
	parser.add_option("--browse", action="store_true", default=False, help=_("start a git browser"))
	parser.add_option("--log", action="store_true", default=False, help=_("prints git log"))
	parser.add_option("--status", action="store_true", default=False, help=_("prints git status"))
	parser.add_option("--ignore", action="store_true", default=False, help=_("recreates list of all ignored files"))
	parser.add_option("--verbose", action="store_true", default=False, help=_("print git output to stdout and set loglevel to DEBUG"))
	parser.add_option("--actions", action="store_true", default=False, help=_("computer-readable actions in persy"))
	parser.add_option("--optimize", action="store_true", default=False, help=_("optimizes the stored files. saves space and improves performance"))
	parser.add_option("--configfile", dest="configfile", default=None, help=_("use a non-default config file"))
	parser.add_option("--config", action="store_true", default=False, help=_("needed flag to change configurations"))
	parser.add_option("--version", action="store_true", default=False, help=_("prints the version"))
	parser.add_option("--uname", dest="uname", default="", help=_("username used in commit"))
	parser.add_option("--mail", dest="mail", default="", help=_("useremail used in commit"))
	parser.add_option("--headless", action="store_true", default=False, help=_("run in headless mode"))
	parser.add_option("--path", dest="path", default="", help=_("path on the server"))
	parser.add_option("--hostname", dest="hostname", default="", help=_("hostname of the remote server"))
	parser.add_option("--add_dir", dest="add_dir", default="", help=_("add local wachted folders"))
	(options, args) = parser.parse_args(args)

	#creat the configuration
	config =  PersyConfig(options.configfile)

	#change in the userhome for all actions
	os.chdir(config.getAttribute('USERHOME'))

	#create programdirectory and a default config file
	if not os.path.exists(config.getAttribute('PERSY_DIR')):
		os.makedirs(config.getAttribute('PERSY_DIR'))

	log = Talker(config, options.verbose) #verbose = print ALL output to stdout
	log.setLevel(options.verbose) #true = debug, false = info set verbosity to show all messages of severity >= DEBUG

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
					config['local']['watched'] = [options.add_dir]
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


	core = Core()
	core.init(config, log)


	#check if a local repository is initialized:
	if not core.isLocalInitialized():
		core.init_local()

	if options.initremote:
		core.initRemote()
	elif options.version:
		persyhelper = PersyHelper()
		print persyhelper.getSoftwareVersion('persy')
	elif options.syncwithremote:
		core.syncWithRemote()
	elif options.browse:
		core.browse()
	elif options.log:
		core.vcslog()
	elif options.status:
		core.vcsstatus()
	elif options.ignore:
		core.vcsignore()
	elif options.optimize:
		core.optimize()
	elif options.actions:
		#this i used for cli completion
		for opt in parser.option_list:
			print opt.get_opt_string(),
		sys.exit(0)
	else:
		#check if all the icons are present, just warn is something is missing
		filestocheck = (config.getAttribute('ICON_IDLE'), config.getAttribute('ICON_OK'),
			config.getAttribute('ICON_UNSYNCED'), config.getAttribute('ICON_UNTRACKED'),
			config.getAttribute('ICON_WARN'), config.getAttribute('ICON_ERROR'), 
			config.getAttribute('LOGO'))
		fileresults = map(os.path.exists, filestocheck)
		i = 0 
		for fileresult in fileresults:
			if not fileresult:
				log.warn(_("%s file is missing!") % filestocheck[i])
			i += 1


		#START!
		if options.headless:
			core.persy_start()
		else:
			pgtk = PersyGtk()
			pgtk.init(core, config, log, options.start)


if __name__ == '__main__':
	try:
		main(sys.argv)
	except Exception as e:
		print 'Unexpected error: ' + str(e)
		raise

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
	import paramiko
	import os
	import subprocess2
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



class PersySSH():
	"""
	Functions that might be helpful for ssh stuff
	"""
	def __init__(self, config, log):
		self.config = config
		self.log = log

	def checkSSHAuth(self):
		"""
		check ifs an connection to the server is possible.
		this function uses the configuration data from the PersyConfig object.
		"""
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		try:
			client.connect(self.config['remote']['hostname'],
							username=self.config['remote']['username'],
							port=int(self.config['remote']['port']))
		except paramiko.PasswordRequiredException as e:
			self.log.critical(str(e))
			return False
		except Exception as e:
			self.log.critical(str(e))
			return False
		return True

	def localSSHKeysExist(self):
		"""
		checks if local ssh keys are generated.
		its is looking for the ..ssh/id_*sa files
		"""
		if os.path.exists(os.path.join(self.config.getAttribute('LOCALSSHDIR'), 'id_rsa')) and os.path.exists(os.path.join(self.config.getAttribute('LOCALSSHDIR'), 'id_rsa.pub')):
			return True
		if os.path.exists(os.path.join(self.config.getAttribute('LOCALSSHDIR'), 'id_dsa')) and os.path.exists(os.path.join(self.config.getAttribute('LOCALSSHDIR'), 'id_dsa.pub')):
			return True
		return False


	def createLocalSSHKeys(self, password):
		"""
		create the local keys.
		this function is not used at the moment and its not testet. 
		a button in the settings gui exists for this function.
		"""
		#create public and private keys
		if not os.path.exists(self.config.getAttribute('LOCALSSHDIR')):
			os.makedirs(self.config.getAttribute('LOCALSSHDIR'))
			os.chmod(self.config.getAttribute('LOCALSSHDIR'), 700)

		if not self.localSSHKeysExist():
			callcmd = []
			callcmd.append('ssh-keygen')
			callcmd.append('-q')
			callcmd.append("-p %s"%password)
			callcmd.append('-f')
			callcmd.append(os.path.join(self.config.getAttribute('LOCALSSHDIR'), 'id_rsa'))
			callcmd.append('-t rsa')
			p = subprocess2.Subprocess2(callcmd)
			os.chmod(os.path.join(self.config.getAttribute('LOCALSSHDIR'), 'id_rsa'), 700)
			os.chmod(os.path.join(self.config.getAttribute('LOCALSSHDIR'), 'id_rsa.pub'), 700)

	def checkRemoteServer(self):
		"""
		connects to the server and is trying to execue 'git show' on the server. 
		returns true if everything worked.
		"""
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		try:
			client.connect(self.config['remote']['hostname'],
							username=self.config['remote']['username'],
							port=int(self.config['remote']['port']))
			stdin1, stdout1, stderr1 = client.exec_command("cd %s && git show" % self.config['remote']['path'])
			stdin1.close()
			client.close()
			if stderr1:
				err = stderr1.read()
				#if something is actually in err
				if not err == '':
					self.log.critical(err)
					return False
		except paramiko.PasswordRequiredException as e:
			self.log.critical(str(e))
			return False
		except Exception as e:
			self.log.critical(str(e))
			return False
		return True

	def publishLocalSSHKeys(self, username, password, hostname):
		"""
		this function is not used (and not implemented yet)
		"""
		pass
		#auf server connecten checken ob das geht mit password! und dann file hinzufügen

		#check on server if file exists
		#HOSTNAME~/.ssh/id_rsa.pub
		#if not, push 
		#scp ~/.ssh/id_rsa.pub HOSTNAME
		#the files now is in ~ on the server

		#check if folder ~/.ssh exists, if not:
		#mkdir ~/.ssh
		#chmod 700 ~/.ssh
		#add the key
		#cat ~/id_rsa.pub >> ~/.ssh/authorized_keys
		#chmod 600 ~/.ssh/authorized_keys
		#clean up
		#rm ~/id_rsa.pub


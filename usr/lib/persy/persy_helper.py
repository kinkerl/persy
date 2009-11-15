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
	import apt_pkg
except ImportError as e:
	print _("You do not have all the dependencies:")
	print str(e)
	sys.exit(1)
except Exception as e:
	print _("An error occured when initialising one of the dependencies!")
	print str(e)
	sys.exit(1)





class _PersyHelper():
	'''Functions that might be helpful in some places
	Uses singleton pattern (see bottom)
	'''

	def __init__(self):
		#aptCache is global for version retrieving
		#this is set with the first call of getSoftwareVersion()
		self.aptCache = None
	

	def getSoftwareVersion(self, name):
		"""returns the version of a installed software as a String. Returns None if not installed"""
		if not self.aptCache:
			print _("using apt-cache to find out about installed apps and versions..")
			apt_pkg.InitConfig()
			apt_pkg.InitSystem()
			self.aptCache = apt_pkg.GetCache()
		try:
			return self.aptCache[name].CurrentVer.VerStr
		except Exception as e:
			return None


#singleton hack
_singleton = _PersyHelper()
def PersyHelper(): return _singleton


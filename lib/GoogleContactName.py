#!/usr/bin/python
# coding: utf8

import json, urllib2, urllib, logging, os, ConfigParser
from GoogleApiOAuth2 import googleOAuth


class googleAPI:

	url = "https://www.google.com/m8/feeds/contacts/default/full?q={0}&alt=json&max-results=1"
	OAuth = None
	
	def getContactName(self, searchString):

		try:

			req = urllib2.Request(self.url.format(urllib.quote_plus(searchString)))
			req.add_header('Gdata-version', "3.0")
			req.add_header('Authorization', self.OAuth.getOAuthKey())

			response = urllib2.urlopen(req)
			contactData = json.loads(response.read())


			if contactData['feed']['openSearch$totalResults']['$t'] == '0':
				logging.debug( 'Contact not found' )
			else:
				logging.debug( 'Contact found' )
				return contactData['feed']['entry'][0]['gd$name']['gd$fullName']['$t'].encode('utf8')
		except urllib2.HTTPError as e:
			logging.error( 'Contact error code:{0}\n'.format(e.code) )
			
			if	e.code == 401: #Get new refresh key
				self.OAuth.forceNew = 2
				self.OAuth.getOAuthKey()
				self.OAuth.forceNew = 0
			
		except  urllib2.URLError as e:
			logging.error( "Error get contact action. With code {0}. \n{1}".format(e.code, e.reason) )
		except:
			logging.error( 'Erorr requesting contact name' )
		
		return ''
		
	def __enter__(self):
		return self
	

	def __exit__(self, exc_type, exc_value, traceback):
		logging.debug( "googleAPI destruct" )
	
	def __init__(self, config, contactName):
		self.contactName = contactName
		self.OAuth = googleOAuth(config, contactName)

if __name__ == "__main__":

	os.chdir(os.path.dirname(__file__))
	os.chdir('..')

	config = ConfigParser.RawConfigParser()
	config.read(os.getcwd()+'/CallerNameResolver.config')
	
	with googleAPI(config, 'default') as contactApi:
		print contactApi.getContactName('+79261554451')
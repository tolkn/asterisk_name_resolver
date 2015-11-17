#!/usr/bin/python
# coding: utf8

import json, urllib2, urllib, logging, os, ConfigParser
from GoogleApiOAuth2 import googleOAuth


class googleAPI:

	config = {}
	
	@staticmethod
	def getContactName(searchString):
		googleOAuth.config = googleAPI.config
		auth = googleOAuth.getOAuthKey(forceNew = 0)

		url = "https://www.google.com/m8/feeds/contacts/default/full?q={0}&alt=json&max-results=1".format(urllib.quote_plus(searchString))

		headers = { 'Gdata-version' : "3.0" ,
					"Authorization" : auth }

		try:

			req = urllib2.Request(url)
			req.add_header('Gdata-version', "3.0")
			req.add_header('Authorization', auth)

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
				os.chdir(os.path.dirname(__file__))
				os.chdir('..')

				googleAPI.config = ConfigParser.RawConfigParser()
				googleAPI.config.read(os.getcwd()+'/CallerNameResolver.config')
				googleOAuth.getOAuthKey(forceNew = 2)
			
		except  urllib2.URLError as e:
			logging.error( "Error get contact action. With code {0}. \n{1}".format(e.code, e.reason) )
		except:
			logging.error( 'Erorr requesting contact name' )
		
		return ''

if __name__ == "__main__":

	os.chdir(os.path.dirname(__file__))
	os.chdir('..')

	googleAPI.config = ConfigParser.RawConfigParser()
	googleAPI.config.read(os.getcwd()+'/CallerNameResolver.config')

	print googleAPI.getContactName(searchString = '+79261554451')
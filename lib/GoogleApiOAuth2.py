#!/usr/bin/python

import io, json, os, datetime
import urllib2, logging, ConfigParser, os

class googleOAuth:

	config = {}

	@staticmethod
	def getOAuthKey(forceNew = 0):
	
		clientId     = googleOAuth.config.get('googleApp', 'clientId')
		clientSecret = googleOAuth.config.get('googleApp', 'clientSecret')
		accessCode   = googleOAuth.config.get('googleApp', 'accessCode')
	

		keyDir = '/usr/share/CallerName'

		keyData = refreshToken = ''

		try:
			with open(keyDir+'/data.txt', 'r') as data_file:
				keyData = json.loads(data_file.read())
				
			refreshToken = keyData['refresh_token']

			expDate = datetime.datetime.strptime(keyData['expires_in'], "%Y-%m-%dT%H:%M:%S.%f")
			
					
			if (datetime.datetime.now()  <= (expDate - datetime.timedelta(minutes=10))) and forceNew == 0:
				logging.debug('Use existing access_token')
				return '{0} {1}'.format(keyData['token_type'], keyData['access_token'])
					
			
		except:
			logging.debug("key data not found")
			

		if forceNew == 2:
			refreshToken = ""
			
			
			
		postData = "client_id={0}&client_secret={1}&".format(clientId, clientSecret) 
		
		if refreshToken == "":
			logging.debug("get new refreshToken by accessCode")
			postData += "code={0}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code".format(accessCode)  
		else:
			postData += "refresh_token={0}&grant_type=refresh_token".format(refreshToken)
					   
					   
		headers = { 'ContentType' : "application/x-www-form-urlencoded" }

		try:

			req = urllib2.Request("https://www.googleapis.com/oauth2/v3/token", postData, headers)
			response = urllib2.urlopen(req)
			keyData = json.loads(response.read())
			
			
			expDate = datetime.datetime.now() + datetime.timedelta(seconds=keyData['expires_in'])
			keyData['expires_in'] = expDate.isoformat()
		
		
			if not hasattr(keyData,'refresh_token') and refreshToken <> '':
				keyData['refresh_token'] = refreshToken
				
			if not os.path.exists(keyDir):
				os.makedirs(keyDir)

			with io.open(keyDir+'/data.txt', 'w', encoding='utf-8') as f:
				f.write(unicode(json.dumps(keyData, ensure_ascii=False)))
					
					
			logging.debug('Get new access_token')
			return '{0} {1}'.format(keyData['token_type'], keyData['access_token'])
		except urllib2.HTTPError as e:
			logging.error( 'OAuth2 error code:{0}\n{1}'.format(e.code, e.fp.read()) )
			
		except  urllib2.URLError as e:
			logging.error( "Error OAuth2 action. With code {0}. \n{1}".format(e.code, e.reason) )
		except:
			logging.error('Error OAuth2 accessToken taken')

			
	
	
if __name__ == "__main__":
	
	os.chdir(os.path.dirname(__file__))
	os.chdir('..')

	googleOAuth.config = ConfigParser.RawConfigParser()
	googleOAuth.config.read(os.getcwd()+'/CallerNameResolver.config')

	print googleOAuth.getOAuthKey()
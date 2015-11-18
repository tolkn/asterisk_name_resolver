#!/usr/bin/python

import io, json, os, datetime
import urllib2, logging, ConfigParser, os

class googleOAuth:

	keyDir = '/usr/share/CallerName'	
	keyData = None
	forceNew = 0

	def getOAuthKey(self):
	
		try:
			
			expDate = datetime.datetime.strptime(self.keyData['expires_in'], "%Y-%m-%dT%H:%M:%S.%f")
				
			if (datetime.datetime.now()  <= (expDate - datetime.timedelta(minutes=10))) and self.forceNew == 0:
				logging.debug('Use existing access_token')
				return '{0} {1}'.format(self.keyData['token_type'], self.keyData['access_token'])
			
		except:
			logging.debug("key data not found")
			

		if self.forceNew == 2:
			self.keyData['refresh_token'] = ""
			
		postData = "client_id={0}&client_secret={1}&".format(self.clientId, self.clientSecret) 
		if self.keyData.get('refresh_token') is None:
			logging.debug("get new refreshToken by accessCode")
			postData += "code={0}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code".format(self.accessCode)  
		else:
			refreshToken = self.keyData['refresh_token']
			postData += "refresh_token={0}&grant_type=refresh_token".format(self.keyData['refresh_token'])
					   
					   
		headers = { 'ContentType' : "application/x-www-form-urlencoded" }
		try:

			req = urllib2.Request("https://www.googleapis.com/oauth2/v3/token", postData, headers)
			response = urllib2.urlopen(req)
			self.keyData = json.loads(response.read())
			
			if self.keyData.get('refresh_token') is None:
				self.keyData['refresh_token'] = refreshToken
			
			expDate = datetime.datetime.now() + datetime.timedelta(seconds=self.keyData['expires_in'])
			self.keyData['expires_in'] = expDate.isoformat()
		
			self.saveKeyData()
			logging.debug('Get new access_token')
			return '{0} {1}'.format(self.keyData['token_type'], self.keyData['access_token'])
		except urllib2.HTTPError as e:
			logging.error( 'OAuth2 error code:{0}\n{1}'.format(e.code, e.fp.read()) )
			
		except  urllib2.URLError as e:
			logging.error( "Error OAuth2 action. With code {0}. \n{1}".format(e.code, e.reason) )
		except:
			logging.error('Error OAuth2 accessToken taken')
			
	def saveKeyData(self):
		if self.keyData <> None:
			if not os.path.exists(self.keyDir):
				os.makedirs(self.keyDir)
		
			with io.open(self.keyDir+'/data.txt', 'w', encoding='utf-8') as f:
				f.write(unicode(json.dumps(self.keyData, ensure_ascii=False)))

	def __init__(self, config):
	
		self.clientId     = config.get('googleApp', 'clientId')
		self.clientSecret = config.get('googleApp', 'clientSecret')
		self.accessCode   = config.get('googleApp', 'accessCode')
	
		logging.debug( "OAuth create" )
		with open(self.keyDir+'/data.txt', 'r') as data_file:
			self.keyData = json.loads(data_file.read())
			
	def __enter__(self):
		return self
	

	def __exit__(self, exc_type, exc_value, traceback):
		self.saveKeyData()
		logging.debug( "OAuth destruct" )
		
	
	
if __name__ == "__main__":
	
	os.chdir(os.path.dirname(__file__))
	os.chdir('..')

	config = ConfigParser.RawConfigParser()
	config.read(os.getcwd()+'/CallerNameResolver.config')
	
	with googleOAuth(config) as oauth:
		oauth.forceNew = 1
		print oauth.getOAuthKey()
		
		
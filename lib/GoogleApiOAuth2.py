#!/usr/bin/python

import io, json, os, datetime
import urllib2, logging, ConfigParser, os

class googleOAuthCommon:
	keyDir = '/usr/share/CallerName'
	contactName = None
	
	def saveKeyData(self, keyData):
		if self.contactName is not None and keyData <> None:
			if not os.path.exists(self.keyDir):
				os.makedirs(self.keyDir)
		
			with io.open('{0}/{1}.txt'.format(self.keyDir, self.contactName), 'w', encoding='utf-8') as f:
				f.write(unicode(json.dumps(keyData, ensure_ascii=False)))
				
	def readKeyData(self):
		keyData = {}
		if self.contactName is not None and os.path.exists('{0}/{1}.txt'.format(self.keyDir, self.contactName)):
			with open('{0}/{1}.txt'.format(self.keyDir, self.contactName), 'r') as data_file:
				keyData = json.loads(data_file.read())
		return keyData

class googleTokenRequest(googleOAuthCommon):
	req = None
	headers = { 'ContentType' : "application/x-www-form-urlencoded" }
	url = '"https://www.googleapis.com/oauth2/v3/token"'
	postData = "client_id={0}&client_secret={1}&"
	
	def getKeyData(self):
		try:
			response = urllib2.urlopen(self.req)
			keyData = json.loads(response.read())
			expDate = datetime.datetime.now() + datetime.timedelta(seconds=keyData['expires_in'])
			keyData['expires_in'] = expDate.isoformat()
			
			return keyData
		except urllib2.HTTPError as e:
			logging.error( 'OAuth2 error code:{0}\n{1}'.format(e.code, e.fp.read()) )
			
		except  urllib2.URLError as e:
			logging.error( "Error OAuth2 action. With code {0}. \n{1}".format(e.code, e.reason) )
		except:
			logging.error('Error OAuth2 accessToken taken')
	
	def __init__(self, clientId, clientSecret):
		self.postData = self.postData.format(clientId, clientSecret) 
		self.req = urllib2.Request("https://www.googleapis.com/oauth2/v3/token", self.postData, self.headers)
	
	def __del__(self):
		if self.req is not None:
			del self.req
			self.req = None
	
class googleRefreshTokenRequest(googleTokenRequest):

	
	def getKeyData(self):
		keyData = googleTokenRequest.getKeyData(self)
		
		self.saveKeyData(keyData)
		
		return keyData

	def __init__(self, clientId, clientSecret, accessCode):
		googleTokenRequest.postData += "code={0}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code".format(accessCode)
		googleTokenRequest.__init__(self, clientId, clientSecret)
		
class googleAccessTokenRequest(googleTokenRequest):
	
	refreshToken = None
	
	def getKeyData(self):
		keyData = googleTokenRequest.getKeyData(self)
		keyData['refresh_token'] = self.refreshToken
		return keyData

	def __init__(self, clientId, clientSecret, refreshToken):
		self.refreshToken = refreshToken
		googleTokenRequest.postData += "refresh_token={0}&grant_type=refresh_token".format(refreshToken)
		googleTokenRequest.__init__(self, clientId, clientSecret)
		
		
	

class googleOAuth(googleOAuthCommon):

	keyData = None
	forceNew = 0
	googleRequest = None
	

	def getOAuthKey(self):
	
		try:
			
			expDate = datetime.datetime.strptime(self.keyData['expires_in'], "%Y-%m-%dT%H:%M:%S.%f")
				
			if (datetime.datetime.now()  <= (expDate - datetime.timedelta(minutes=10))) and self.forceNew == 0:
				logging.debug('Use existing access_token')
				return '{0} {1}'.format(self.keyData['token_type'], self.keyData['access_token'])
			
		except:
			logging.debug("key data not found")
			

		if self.forceNew == 2 or self.keyData.get('refresh_token') is None:
			self.googleRequest = googleRefreshTokenRequest(self.clientId, self.clientSecret, self.accessCode)
		elif self.googleRequest is None:
			self.googleRequest = googleAccessTokenRequest(self.clientId, self.clientSecret, self.keyData['refresh_token'])
			
		self.googleRequest.contactName = self.contactName

		kd = self.googleRequest.getKeyData()	
		if self.forceNew == 2 or self.keyData.get('refresh_token') is None:
			self.googleRequest = None
		
		self.keyData = kd
			
		logging.debug('Get new access_token')
		return '{0} {1}'.format(self.keyData['token_type'], self.keyData['access_token'])
		
	

	def __init__(self, config, contactName):
	
		self.contactName = contactName
		self.clientId     = config.get('googleApp', 'clientId')
		self.clientSecret = config.get('googleApp', 'clientSecret')
		self.accessCode   = config.get('contact_'+contactName, 'accessCode')
	
		logging.debug( "OAuth create for '{0}' contact context".format(contactName) )
		self.keyData = self.readKeyData()
			
	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		if self.keyData is not None:
			self.saveKeyData(self.keyData)
			self.keyData = None
		logging.debug( 'exit' )
		
	def __del__(self):
		if self.googleRequest is not None:
			del self.googleRequest
			
		if self.keyData is not None:
			self.saveKeyData(self.keyData)
			self.keyData = None
		logging.debug( 'Destruct oauth' )
		

	
	
if __name__ == "__main__":
	
	os.chdir(os.path.dirname(__file__))
	os.chdir('..')

	config = ConfigParser.RawConfigParser()
	config.read(os.getcwd()+'/CallerNameResolver.config')

	
	with googleOAuth(config, '888') as oauth:
#		oauth.forceNew = 1
		print oauth.getOAuthKey()
	
	oauth = googleOAuth(config, '888')
	del oauth
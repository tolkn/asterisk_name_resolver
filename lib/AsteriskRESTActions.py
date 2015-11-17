#!/usr/bin/python

import urllib2, base64, logging, ConfigParser, os


class asteriskRESTActions:

	config = {}

	@staticmethod
	def ari_channel_action(channel_id, action, data=''):
			
		
		ari_url   = asteriskRESTActions.config.get('default', 'ari_url')
		ari_login = asteriskRESTActions.config.get('default', 'ari_login')
		ari_pass  = asteriskRESTActions.config.get('default', 'ari_pass')
		
		url = 'http://{0}/ari/channels/{1}/{2}'.format(ari_url, channel_id, action)	
		
		
		headers = { 'ContentType' : "application/json" }
		try:
		
			req = urllib2.Request(url, data, headers)
			base64string = base64.encodestring('%s:%s' % (ari_login, ari_pass)).replace('\n', '')
			req.add_header("Authorization", "Basic %s" % base64string) 
			response = urllib2.urlopen(req)
			
			logging.debug("REST Action done:{0}".format(action))
		except urllib2.HTTPError as e:
			logging.error('ARI HTTPerror')
			logging.error( 'ARI service error code:{0}\n{1}'.format(e.code, e.fp.read()) )
			
		except  urllib2.URLError as e:
			logging.error('ARI URLerror')
			logging.error( "Error ari action. With code {0}. \n{1}".format(e.code, e.reason) )

	@staticmethod
	def set_channel_caller_name(channel_id, name):
		
		postData = "variable=CALLERID(name)&value='{0}'".format(name) 
		asteriskRESTActions.ari_channel_action(channel_id, 'variable', postData)
	
	@staticmethod
	def set_continue(channel_id):
		asteriskRESTActions.ari_channel_action(channel_id, 'continue')

if __name__ == "__main__":

	os.chdir(os.path.dirname(__file__))
	os.chdir('..')

	asteriskRESTActions.config = ConfigParser.RawConfigParser()
	asteriskRESTActions.config.read(os.getcwd()+'/CallerNameResolver.config')

	asteriskRESTActions.set_continue('1447506846.22')
	asteriskRESTActions.set_channel_caller_name('1447506846.22', 'test')
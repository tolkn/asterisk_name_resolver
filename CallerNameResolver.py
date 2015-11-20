#!/usr/bin/python
# coding: utf8

import websocket
import thread
import time
import json
import sys, os
import daemon
import daemon.pidfile
import logging
import ConfigParser

sys.path.append(os.path.dirname(__file__)+'/lib')
from GoogleContactName import googleAPI
from AsteriskRESTActions import asteriskRESTActions
from GoogleApiOAuth2 import googleOAuth
from daemon import runner
from translit import transliterate

logDir = "/var/log/asterisk_name_resolver"
logFormat = "[%(asctime)s] %(levelname)s {%(filename)s:%(lineno)d} - %(message)s"
logLevel = logging.DEBUG

class caller_name_resolver:

	ws = None
	mode = 0
	config = None
	contactDic = {}

	def on_message(self, ws, message):
		msg = json.loads(message)
		if msg['type'] == 'StasisStart':
			logging.debug( u"type={0}:channel_id={1}:caller_id={2}:caller_name={3}:target_number={4}".format(msg['type'], msg['channel']['id'], msg['channel']['caller']['number'], msg['channel']['caller']['name'], msg['channel']['dialplan']['exten']))
									
			number = msg['channel']['caller']['number']
			numberLen = len(number)
			if numberLen > 10:
				number = number[numberLen-10:] #Find by last 10 digit
			
			
			currentContactContext = self.contactDic.get(msg['channel']['dialplan']['exten'])
			if	currentContactContext == None:
				currentContactContext = self.contactDic.get('default')

			if	currentContactContext <> None:
				logging.debug( "Using contact context:{0}".format(currentContactContext.contactName) )
				name = currentContactContext.getContactName(number)
				if name <> '':
					logging.info( u'Found GoogleContact: {0} by caller number: {1}'.format(name.decode('utf8'), msg['channel']['caller']['number'])  )
					logging.debug( "Set contact name to channel " )
					if msg['args'] <> []:
						if msg['args'][0].strip() == 'useTranslit':
							name = u"%s" % transliterate(name.decode('utf8'))
							logging.debug( u"Transliterate name: %s" % name)
					
					self.asteriskAction.set_channel_caller_name(msg['channel']['id'], name)
			else:
				logging.debug( "Not found contact context" )
				
			logging.debug( "Set dialplan continue " )	
			self.asteriskAction.set_continue(msg['channel']['id'])
		
		elif msg['type'] == 'ChannelCallerId':
			logging.debug( u"type={0}:channel_id={1}:caller_id={2}:caller_name={3}:target_number={4}".format(msg['type'], msg['channel']['id'], msg['channel']['caller']['number'], msg['channel']['caller']['name'], msg['channel']['dialplan']['exten']))
		else:
			logging.debug( u"type={0}:channel_id={1}:caller_id={2}:caller_name={3}:target_number={4}".format(msg['type'], msg['channel']['id'], msg['channel']['caller']['number'], msg['channel']['caller']['name'], msg['channel']['dialplan']['exten']))
		

	def on_error(self, ws, error):
		logging.error( "### error ###:{0}".format(error) )

	def on_close(self, ws):
		logging.debug( "### closed ###" )

	def on_open(self, ws):
		logging.debug( "### open ###" )
		
	def run(self):
		

		if self.ws is None:
			ari_url   = self.config.get('default', 'ari_url')
			ari_login = self.config.get('default', 'ari_login')
			ari_pass = self.config.get('default', 'ari_pass')
			
			
			if self.mode == 1:
				websocket.enableTrace(True)
				
			try:
			
				self.ws = websocket.WebSocketApp("ws://{0}/ari/events?api_key={1}:{2}&app=NameResolver".format(ari_url, ari_login, ari_pass),
									  on_message = self.on_message,
									  on_error = self.on_error,
									  on_close = self.on_close)

				self.ws.on_close = self.on_close

				logging.info( "Service start " )
				logging.info( "-=============================================================================================-" )
				
				
				self.ws.run_forever()
			
			except:
				logging.debug( 'Erorr websocket:' )
			finally:
				if self.ws is not None:
					logging.debug( "Socket close" )
					self.ws.close()
					self.ws = None

	
	
	def __init__(self, config=None, action=None):
	
		self.asteriskAction = action
				
		if config is not None:
			self.config = config
			
			for sec in config.sections():
				names = sec.rsplit('contact_')
				if (len(names) == 2 and (dict(config.items(sec))).get('accesscode') <> None):
					self.contactDic[names[1]] = googleAPI(config, names[1])
	
		
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty'
		self.stderr_path = '/dev/tty'
		self.pidfile_path =  '/var/run/CallerNameResolver.pid'
		self.pidfile_timeout = 5		
		
	def __enter__(self):
		return self
	

	def __exit__(self, exc_type, exc_value, traceback):
		logging.debug( "Service exit " )
		
	def __del__(self):
		if self.contactDic <> None:
			for x in self.contactDic:
				del x
			self.contactDic = None
		
		if self.asteriskAction <> None:
			del self.asteriskAction
			self.asteriskAction = None
		
			if self.ws is not None:
				logging.debug( "Socket close" )
				self.ws.close()
				del self.ws
				self.ws = None
			logging.info( "-=============================================================================================-" )
			logging.info( "Service destruct" )


if __name__ == "__main__":
	
	config = ConfigParser.RawConfigParser()
	config.read(os.path.dirname(__file__)+'/CallerNameResolver.config')
	
	if	config.get('default', 'log_level') == 'INFO':
		logLevel = logging.INFO
		
	
	if len(sys.argv) > 1:
	
		if not os.path.exists(logDir):
			os.makedirs(logDir)

		handler = logging.FileHandler(logDir+'/message.log', "a", encoding = "UTF-8")
		formatter = logging.Formatter(logFormat)
		handler.setFormatter(formatter)
		root_logger = logging.getLogger()
		root_logger.addHandler(handler)
		root_logger.setLevel(logLevel)
	
		if sys.argv[1] == 'start':
					
			action = asteriskRESTActions(config)
			with caller_name_resolver(config, action) as instance:
				daemon_runner = runner.DaemonRunner(instance)
				daemon_runner.daemon_context.files_preserve=[handler.stream]
				daemon_runner.do_action()
				
		elif sys.argv[1] == 'stop':
	
			instance =  caller_name_resolver()
			daemon_runner = runner.DaemonRunner(instance)
			daemon_runner.daemon_context.files_preserve=[handler.stream]
			daemon_runner.do_action()


	else:
		logging.basicConfig(format = logFormat, level = logLevel)
		action = asteriskRESTActions(config)
		with caller_name_resolver(config, action) as instance:
			instance.mode = 1
			instance.run()



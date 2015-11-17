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


config = ConfigParser.RawConfigParser()
config.read(os.path.dirname(__file__)+'/CallerNameResolver.config')

ari_url   = config.get('default', 'ari_url')
ari_login = config.get('default', 'ari_login')
ari_pass = config.get('default', 'ari_pass')


logDir = "/var/log/asterisk_name_resolver"
logFormat = "[%(asctime)s] %(levelname)s {%(filename)s:%(lineno)d} - %(message)s"

if	config.get('default', 'log_level') == 'INFO':
	logLevel = logging.INFO
else:
	logLevel = logging.DEBUG


asteriskRESTActions.config = config
googleAPI.config = config

def on_message(ws, message):

	msg = json.loads(message)
	if msg['type'] == 'StasisStart':
		logging.debug( u"type={0}:channel_id={1}:caller_id={2}:caller_name={3}".format(msg['type'], msg['channel']['id'], msg['channel']['caller']['number'], msg['channel']['caller']['name']))
		
		number = msg['channel']['caller']['number']
		numberLen = len(number)
		if numberLen > 10:
			number = number[numberLen-10:] #Find by last 10 digit
		
		name = googleAPI.getContactName(number)
		if name <> '':
			logging.info( u'Found GoogleContact: {0} by caller number: {1}'.format(name.decode('utf8'), msg['channel']['caller']['number'])  )
			logging.debug( "Set contact name to channel " )
			asteriskRESTActions.set_channel_caller_name(msg['channel']['id'], name)
		
		logging.debug( "Set dialplan continue " )	
		asteriskRESTActions.set_continue(msg['channel']['id'])
		
	elif msg['type'] == 'ChannelCallerId':
		logging.debug( u"type={0}:channel_id={1}:caller_id={2}:caller_name={3}".format(msg['type'], msg['channel']['id'], msg['channel']['caller']['number'], msg['channel']['caller']['name']))
	else:
		logging.debug( u"type={0}:channel_id={1}:caller_id={2}:caller_name={3}".format(msg['type'], msg['channel']['id'], msg['channel']['caller']['number'], msg['channel']['caller']['name']))
	

def on_error(ws, error):
    logging.error( "### error ###:{0}".format(error) )

def on_close(ws):
    logging.debug( "### closed ###" )

def on_open(ws):
	logging.debug( "### open ###" )
    
def run(mode=1):
	
	if mode == 1:
		websocket.enableTrace(True)
	ws = websocket.WebSocketApp("ws://{0}/ari/events?api_key={1}:{2}&app=NameResolver".format(ari_url, ari_login, ari_pass),
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)

	ws.on_close = on_close
	try:
		ws.run_forever()
	except:
		logging.error( 'Erorr websocket' )
	finally:
		ws.close()

	
def run_daemon():

	if not os.path.exists(logDir):
		os.makedirs(logDir)

	handler = logging.FileHandler(logDir+'/message.log', "a", encoding = "UTF-8")
	formatter = logging.Formatter(logFormat)
	handler.setFormatter(formatter)
	root_logger = logging.getLogger()
	root_logger.addHandler(handler)
	root_logger.setLevel(logLevel)

	logging.info( "-=============================================================================================-" )
	logging.info( "Service start " )
	
	try:
		with daemon.DaemonContext(pidfile=daemon.pidfile.PIDLockFile('/var/run/CallerNameResolver.pid'), files_preserve = [handler.stream]):
			run(0)
	except:
		logging.error( 'Erorr daemon' )
	finally:
		logging.debug( "Service stop " )



if __name__ == "__main__":

	if len(sys.argv) > 1 and  sys.argv[1] == 'DAEMON':
		
		run_daemon()
	else:
		logging.basicConfig(format = logFormat, level = logLevel)
		run()
	


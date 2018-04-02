#!/usr/bin/python
################################################################################
# MESSAGING
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 10/16/2016 Original construction
# 10/10/2017 Updated timestamps to be human readable
################################################################################

import cherrypy
import json

from threading import Lock
from time import time, strftime, localtime

global global_messages
global global_messages_lock
global_messages = {"messages":[]}
global_messages_lock = Lock()

def add_message(message, timestamp = None):
    if not timestamp:
        timestamp = time()
    
    global_messages_lock.acquire()
    global_messages["messages"] = [{"message" : message, "timestamp" : strftime('%H:%M:%S', localtime(timestamp))}] + \
                                    global_messages["messages"][:49]
    global_messages_lock.release()

def get_messages():
    global_messages_lock.acquire()
    messages = global_messages
    global_messages_lock.release()
    return messages

class Messaging(object):
    def __init__(self):
        self.messages = {"messages":[]}
    
    @cherrypy.expose
    def ajax_add_message(self, message, timestamp):
        add_message(message, timestamp)
        return json.dumps({})
    
    @cherrypy.expose
    def ajax_add_message(self, message):
        add_message(message)
        return json.dumps({})
    
    @cherrypy.expose
    def ajax_get_messages(self):
        return json.dumps(get_messages())
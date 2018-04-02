#!/usr/bin/python
################################################################################
# FLAGS
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 12/06/2016 Original construction
################################################################################

import cherrypy
import json

from threading import Lock
from random import random

global global_flags
global global_flag_lock
global_flags = {}
global_flag_lock = Lock()

def set_flag(key, value):
    global_flag_lock.acquire()
    global_flags[key] = value
    global_flag_lock.release()
    return value

def get_flag(key):
    try:
        global_flag_lock.acquire()
        global_flags[key]
    except KeyError:
        global_flags[key] = None
    finally:
        global_flag_lock.release()
        return global_flags[key]

def touch_flag(key):
    return set_flag(key, random())

class Flags(object):
    @cherrypy.expose
    def ajax_set(self, key, value):
        return json.dumps({"key" : key, "value" : set_flag(key, value)})
    
    @cherrypy.expose
    def ajax_get(self, key):
        return json.dumps({"key" : key, "value" : get_flag(key)})
    
    @cherrypy.expose
    def ajax_touch(self, key):
        return json.dumps({"key" : key, "value" : touch_flag(key)})
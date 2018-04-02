#!/usr/bin/python
################################################################################
# TERMINAL
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 01/09/2017 Original construction
################################################################################

CLI_TIME_OUT = 5 * 60
RECV_TIME_OUT = 60

import traceback

from threading import Lock, Thread
from imp import new_module
from time import time, sleep

from ..controller.messaging import add_message

from .document import Collection
from .utils import sucky_uuid

global cli_sessions
cli_sessions = {}

class ErrorConsole:
    def __init__(self, message):
        self.__buffer = message
    
    def send(self, input_buffer):
        pass
    
    def recv(self):
        output_buffer = self.__buffer
        self.__buffer = ''
        return output_buffer

def send(ttyuuid, buffer):
    try:
        cli_sessions[ttyuuid]["contact"] = time()
        cli_sessions[ttyuuid]["console"].send(buffer)
    except Exception:
        add_message(traceback.format_exc())

def recv(ttyuuid):
    try:
        cli_sessions[ttyuuid]["contact"] = time()
        return cli_sessions[ttyuuid]["console"].recv()
    except Exception:
        add_message(traceback.format_exc())
        return traceback.format_exc()

def write_file(ttyuuid, file):
    try:
        cli_sessions[ttyuuid]["console"].putf(file)
        cli_sessions[ttyuuid]["contact"] = time()
    except Exception:
        add_message(traceback.format_exc())
        
def create_session(hstuuid, session):
    try:
        ttyuuid = sucky_uuid()
       
        inventory = Collection("inventory")
        host = inventory.get_object(hstuuid)
        tempmodule = new_module("tempmodule")
        exec inventory.get_object(host.object["console"]).object["body"] in tempmodule.__dict__
        
        if "send" not in dir(tempmodule.Console):
            raise Exception, "send method not present in console object!"
        
        if "recv" not in dir(tempmodule.Console):
            raise Exception, "recv method not present in console object!"
        
        cli_sessions[ttyuuid] = {}
        cli_sessions[ttyuuid]["console"] = tempmodule.Console(session = session, host = host.object)
        cli_sessions[ttyuuid]["contact"] = time()
    except Exception:
        cli_sessions[ttyuuid] = {}
        cli_sessions[ttyuuid]["console"] = ErrorConsole(traceback.format_exc())
        cli_sessions[ttyuuid]["contact"] = time()
        add_message(traceback.format_exc())
    finally:
        Thread(target = time_out_worker, args = (ttyuuid,)).start()
        return ttyuuid

def destroy_session(ttyuuid):
    try:
        try:
            cli_sessions[ttyuuid]["console"].close()
        except Exception:
            add_message(traceback.format_exc())
        finally:
            del cli_sessions[ttyuuid]
    except Exception:
        add_message(traceback.format_exc())
        
def time_out_worker(ttyuuid):
    try:
        if time() - cli_sessions[ttyuuid]["contact"] > CLI_TIME_OUT:
            add_message("terminal model: ttyuuid {0} closed due to inactivity".format(ttyuuid))
            destroy_session(ttyuuid)
        else:
            sleep(60)
            Thread(target = time_out_worker, args = (ttyuuid,)).start()
    except Exception:
        pass
        #add_message(traceback.format_exc())
#!/usr/bin/python
################################################################################
# HTTPS INTERFACE
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 07/27/2017 Original construction
################################################################################

SESSION_TIMEOUT = 90

import json
import traceback
import ssl
import hashlib
import httplib
import urllib2

from threading import Lock, Thread, Timer
from time import time, sleep
from ..controller.messaging import add_message

global https_sessions
https_sessions = {}

def create_session(url):
    trys = 0
    
    while trys < 3:
        try:
            trys += 1
            
            req = urllib2.Request(url = url)
        
            https_sessions[url] = {}
            https_sessions[url]["lock"] = Lock()
            https_sessions[url]["contact"] = time()
            https_sessions[url]["full url"] = req.get_full_url()    
            https_sessions[url]["connection"] = httplib.HTTPSConnection(req.get_host(), \
                                                                        context = ssl._create_unverified_context(), \
                                                                        timeout = 15)
            
            return True
        except Exception:
            add_message(traceback.format_exc())
            del https_sessions[url]
            sleep(1)
    
    raise Exception(str(traceback.format_exc()))

def destroy_session(url):
    try:
        https_sessions[url]["connection"].close()
    except Exception:
        add_message(traceback.format_exc())
    del https_sessions[url]

def send_json(url, json_in, secret_digest):
    if url not in https_sessions:
        create_session(url)

    raw_json_in = json.dumps(json_in)
    
    h = hashlib.sha256()
    h.update(secret_digest)
    h.update(raw_json_in)
    
    headers = {
        'Content-Type' : 'application/json',
        'Signature' : h.hexdigest()
    }
    
    trys = 0
    
    while trys < 3:
        try:
            trys += 1
            
            https_sessions[url]["lock"].acquire()
            https_sessions[url]["contact"] = time()
            https_sessions[url]["connection"].request("POST", \
                                                      https_sessions[url]["full url"], \
                                                      raw_json_in, \
                                                      headers)
            response = https_sessions[url]["connection"].getresponse()
            signature = response.getheader("Signature")
            raw_json_out = response.read()
            https_sessions[url]["lock"].release()
            
            h = hashlib.sha256()
            h.update(secret_digest)
            h.update(raw_json_out)
    
            if h.hexdigest() != signature:
                raise Exception("Signature mismatch encountered!")
            
            return json.loads(raw_json_out)
        except Exception:
            add_message(traceback.format_exc())
            https_sessions[url]["lock"].release()
            destroy_session(url)
            sleep(1)
    
    raise Exception(str(traceback.format_exc()))
    
def worker():
    Timer(60.0, worker).start()

    try:
        stale_urls = []
        
        for k, v in https_sessions.iteritems():
            try:
                if time() - v["contact"] > SESSION_TIMEOUT:
                    stale_urls.append(k)
            except Exception:
                stale_urls.append(k)
        
        for url in stale_urls:
            destroy_session(url)

    except Exception:
        add_message(traceback.format_exc())
    
Thread(target = worker).start()
#!/usr/bin/python
################################################################################
# TERMINAL
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 01/09/2017 Original construction
# 02/22/2017 Updated create session to pull session data from user objects
################################################################################

import cherrypy
import json
import traceback

from cherrypy.lib.static import serve_fileobj

from .messaging import add_message
from ..model.document import Collection
from ..model.terminal import create_session, \
                             destroy_session, \
                             write_file, \
                             send, \
                             recv
from ..model.eventlog import create_terminal_upload_event, \
                             create_terminal_event

class Terminal(object):
    @cherrypy.expose
    def ajax_create_session(self, hstuuid):
        add_message("terminal controller: create terminal")
        try:
            create_terminal_event(Collection("users").find(sessionid = cherrypy.session.id)[0], \
                                  Collection("inventory").get_object(hstuuid))
            
            return json.dumps({"ttyuuid" : create_session(hstuuid, Collection("users").find(sessionid = cherrypy.session.id)[0].object)})
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_destroy_session(self, ttyuuid):
        add_message("terminal controller: destroy terminal: {0}".format(ttyuuid))
        try:
            destroy_session(ttyuuid)
            return json.dumps({})
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_send(self, ttyuuid, buffer):
        try:
            send(ttyuuid, buffer)
            return json.dumps({})
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_recv(self, ttyuuid):
        try:
            return recv(ttyuuid)
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def put_file(self, file, ttyuuid):
        add_message("terminal controller: upload file: {0}".format(file.filename))
        
        try:
            write_file(ttyuuid, file)
        except Exception:
            add_message(traceback.format_exc())
        
        create_terminal_upload_event(Collection("users").find(sessionid = cherrypy.session.id)[0], file.filename)
        
        return json.dumps({})
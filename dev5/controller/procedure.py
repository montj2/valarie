#!/usr/bin/python
################################################################################
# PROCEDURE
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 10/16/2016 Original construction
# 02/22/2017 Updated execute methods to pull session data from user objects
################################################################################

import cherrypy
import json
import traceback

from .messaging import add_message
from ..model.document import Collection
from ..model.procedure import get_task_grid, \
                              get_host_grid, \
                              get_jobs_grid, \
                              queue_procedure, \
                              run_procedure

class Procedure(object):
    @cherrypy.expose
    def ajax_get_task_grid(self, objuuid):
        add_message("procedure controller: get procedure task grid: {0}".format(objuuid))
        try:
            return json.dumps(get_task_grid(objuuid))
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_get_host_grid(self, objuuid):
        add_message("procedure controller: get procedure host grid: {0}".format(objuuid))
        try:
            return json.dumps(get_host_grid(objuuid))
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_execute_procedure(self, prcuuid, hstuuid):
        add_message("procedure controller: execute procedure: hstuuid: {0}, prcuuid: {1}".format(hstuuid, prcuuid))
        try:
            return json.dumps(run_procedure(hstuuid, prcuuid, Collection("users").find(sessionid = cherrypy.session.id)[0].object))
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_queue_procedure(self, prcuuid, hstuuid):
        add_message("procedure controller: queuing procedure: hstuuid: {0}, prcuuid: {1}".format(hstuuid, prcuuid))
        try:
            queue_procedure(hstuuid, prcuuid, Collection("users").find(sessionid = cherrypy.session.id)[0].object)
            return json.dumps({})
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_queue_procedures(self, queuelist):
        try:
            for item in json.loads(queuelist):
                try:
                    add_message("procedure controller: queuing procedure: hstuuid: {0}, prcuuid: {1}".format(item["hstuuid"], item["prcuuid"]))
                    queue_procedure(item["hstuuid"], item["prcuuid"], Collection("users").find(sessionid = cherrypy.session.id)[0].object)
                except Exception:
                    add_message(traceback.format_exc())
        
            return queuelist
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_get_queue_grid(self):
        try:
            return json.dumps(get_jobs_grid())
        except Exception:
            add_message(traceback.format_exc())
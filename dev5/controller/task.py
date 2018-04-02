#!/usr/bin/python
################################################################################
# TASK
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/30/2016 Original construction
# 02/22/2017 Updated execute methods to pull session data from user objects
################################################################################

import cherrypy
import json
import traceback

from ..model.task import get_host_grid, execute
from ..model.document import Collection
from .messaging import add_message

class Task(object):
    @cherrypy.expose
    def ajax_get_host_grid(self, objuuid):
        add_message("task controller: get task host grid: {0}".format(objuuid))
        try:
            return json.dumps(get_host_grid(objuuid))
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_execute_task(self, tskuuid, hstuuid):
        add_message("task controller: execute task: hstuuid: {0}, tskuuid: {1}".format(hstuuid, tskuuid))
        try:
            return json.dumps(execute(tskuuid, hstuuid, Collection("users").find(sessionid = cherrypy.session.id)[0].object))
        except Exception:
            add_message(traceback.format_exc())
        
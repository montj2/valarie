#!/usr/bin/python
################################################################################
# CONTROLLER
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/23/2016 Original construction
################################################################################

import cherrypy
import json
import traceback

from threading import Thread

from ..model.controller import get_procedure_grid, get_host_grid, get_tiles
from .messaging import add_message

class Controller(object):
    @cherrypy.expose
    def ajax_get_procedure_grid(self, objuuid):
        add_message("controller controller: get controller procedure grid: {0}".format(objuuid))
        try:
            return json.dumps(get_procedure_grid(objuuid))
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_get_host_grid(self, objuuid):
        add_message("controller controller: get controller host grid: {0}".format(objuuid))
        try:
            return json.dumps(get_host_grid(objuuid))
        except Exception:
            add_message(traceback.format_exc())
        
    @cherrypy.expose
    def ajax_get_tiles(self, objuuid):
        add_message("controller controller: get controller tiles: {0}".format(objuuid))
        try:
            return json.dumps(get_tiles(objuuid))
        except Exception:
            add_message(traceback.format_exc())

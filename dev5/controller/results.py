#!/usr/bin/python
################################################################################
# RESULTS
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 12/06/2016 Original construction
################################################################################

import cherrypy
import json
import traceback

from .messaging import add_message
from ..model.results import get_controller_results, \
                            get_procedure_result

class Results(object):
    @cherrypy.expose
    def ajax_get_controller(self, objuuid):
        add_message("results controller: get controller results: {0}".format(objuuid))
        try:
            return json.dumps(get_controller_results(objuuid))
        except Exception:
            add_message(traceback.format_exc())
    
    @cherrypy.expose
    def ajax_get_procedure(self, prcuuid, hstuuid):
        add_message("results controller: get procedure result: prcuuid: {0}, hstuuid: {1}".format(prcuuid, hstuuid))
        try:
            return json.dumps(get_procedure_result(prcuuid, hstuuid))
        except Exception:
            add_message(traceback.format_exc())
#!/usr/bin/python
################################################################################
# PROCEDURE
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

from .messaging import add_message
from ..model.rfc import get_rfc_grid

class RFC(object):
    @cherrypy.expose
    def ajax_get_rfc_grid(self, objuuid):
        add_message("RFC controller: get RFC grid: {0}".format(objuuid))
        try:
            return json.dumps(get_rfc_grid(objuuid))
        except Exception:
            add_message(traceback.format_exc())
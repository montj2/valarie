#!/usr/bin/python
################################################################################
# HOST
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/28/2016 Original construction
################################################################################

import cherrypy
import json
import traceback

from ..model.console import get_consoles
from .messaging import add_message

class Console(object):
    @cherrypy.expose
    def ajax_get_consoles(self):
        add_message("console controller: get console objects...")
        try:
            return json.dumps(get_consoles())
        except Exception:
            add_message(traceback.format_exc())
#!/usr/bin/python
################################################################################
# HOST GROUP
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 06/12/2017 Original construction
################################################################################

import cherrypy
import json
import traceback

from ..model.hostgroup import get_host_grid
from ..model.document import Collection
from .messaging import add_message

class HostGroup(object):
    @cherrypy.expose
    def ajax_get_host_grid(self, objuuid):
        add_message("host group controller: get task host grid: {0}".format(objuuid))
        try:
            return json.dumps(get_host_grid(objuuid))
        except Exception:
            add_message(traceback.format_exc())
#!/usr/bin/python
################################################################################
# EVENT LOG
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 04/27/2017 Original construction
################################################################################

import cherrypy
import traceback

from ..model.eventlog import get_events_str
from .messaging import add_message

class EventLog(object):
    @cherrypy.expose
    def ajax_get_events_str(self, max_age):
        add_message("eventlog controller: get events")
        try:
            return get_events_str(int(max_age))
        except Exception:
            add_message(traceback.format_exc())        
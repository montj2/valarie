#!/usr/bin/python
################################################################################
# ROOT
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 10/16/2016 Original construction
################################################################################

import cherrypy
import traceback

from ..view.index import index_view

from .inventory import Inventory
from .messaging import Messaging
from .hostgroup import HostGroup
from .procedure import Procedure
from .controller import Controller
from .eventlog import EventLog
from .console import Console
from .rfc import RFC
from .results import Results
from .flags import Flags
from .task import Task
from .terminal import Terminal
from .auth import Auth, require, member_of

class Root(object):
    inventory = Inventory()
    messaging = Messaging()
    procedure = Procedure()
    controller = Controller()
    console = Console()
    rfc = RFC()
    results = Results()
    flags = Flags()
    task = Task()
    auth = Auth()
    terminal = Terminal()
    eventlog = EventLog()
    hostgroup = HostGroup()
    
    @cherrypy.expose
    @require()
    def index(self):
        return index_view()
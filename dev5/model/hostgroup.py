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

import traceback

from .document import Collection
from ..controller.messaging import add_message

def get_host_grid(grpuuid):
    collection = Collection("inventory")
    
    group = collection.get_object(grpuuid)
    
    grid_data = []
    
    for hstuuid in group.object["hosts"]:
        host = collection.get_object(hstuuid)
        
        if "type" in host.object:
            if host.object["type"] == "host":
                grid_data.append({"type" : host.object["type"], \
                                  "name" : host.object["name"], \
                                  "host" : host.object["host"], \
                                  "objuuid" : host.object["objuuid"]})
            elif host.object["type"] == "host group":
                hosts = []
                
                for uuid in host.object["hosts"]:
                    h = collection.get_object(uuid)
                    
                    if "type" in h.object:
                        if h.object["type"] == "host":
                            hosts.append("{0} ({1})".format(h.object["name"], \
                                                            h.object["host"]))
                        elif h.object["type"] == "host group":
                            hosts.append(h.object["name"])
                    else:
                        host.object["hosts"].remove(uuid)
                        host.set()
                        h.destroy()
                        
                
                grid_data.append({"type" : host.object["type"], \
                                  "name" : host.object["name"], \
                                  "host" : str("<br>").join(hosts), \
                                  "objuuid" : host.object["objuuid"]})
        else:
            add_message("host {0} is missing!".format(hstuuid))
            #grid_data.append({"name" : "MISSING!", "host" : "?.?.?.?", "objuuid" : hstuuid})
            host.destroy()
            group.object["hosts"].remove(hstuuid)
            group.set()
        
    return grid_data
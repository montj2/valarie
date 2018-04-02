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

from threading import Thread

from .document import Collection
from .utils import sucky_uuid
from ..controller.messaging import add_message

def get_procedure_grid(ctruuid):
    collection = Collection("inventory")
    
    controller = collection.get_object(ctruuid)
    
    grid_data = []
    
    for prcuuid in controller.object["procedures"]:
        procedure = collection.get_object(prcuuid)
        
        if "type" in procedure.object:
            grid_data.append({"name" : procedure.object["name"], "objuuid" : procedure.object["objuuid"]})
        else:
            add_message("procedure {0} is missing!".format(prcuuid))
            grid_data.append({"name" : "MISSING!", "objuuid" : prcuuid})
        
    return grid_data

def get_host_grid(ctruuid):
    collection = Collection("inventory")
    
    controller = collection.get_object(ctruuid)
    
    grid_data = []
    
    for hstuuid in controller.object["hosts"]:
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
                    c = collection.get_object(uuid)
                    if "name" in c.object:
                        hosts.append(c.object["name"])
                    else:
                        host.object["hosts"].remove(uuid)
                        host.set()
                        c.destroy()
                
                grid_data.append({"type" : host.object["type"], \
                                  "name" : host.object["name"], \
                                  "host" : str("<br>").join(hosts), \
                                  "objuuid" : host.object["objuuid"]})
        else:
            add_message("host {0} is missing!".format(hstuuid))
            #grid_data.append({"name" : "MISSING!", "host" : "?.?.?.?", "objuuid" : hstuuid})
            host.destroy()
            controller.object["hosts"].remove(hstuuid)
            controller.set()
        
    return grid_data

def get_hosts(hstuuid, hstuuids, grpuuids, inventory):
    o = inventory.get_object(hstuuid)
    
    if "type" in o.object:
        if o.object["type"] == "host":
            if hstuuid not in hstuuids:
                hstuuids.append(hstuuid)
        elif o.object["type"] == "host group":
            for uuid in o.object["hosts"]:
                c = inventory.get_object(uuid)
                if "type" in c.object:
                    if c.object["type"] == "host group":
                        if uuid not in grpuuids:
                            grpuuids.append(uuid)
                            get_hosts(uuid, hstuuids, grpuuids, inventory)
                    elif c.object["type"] == "host":
                        if uuid not in hstuuids:
                            hstuuids.append(uuid)
                else:
                    o.object["hosts"].remove(uuid)
                    o.set()
                    c.destroy()
    
def get_tiles(ctruuid):
    collection = Collection("inventory")
    
    controller = collection.get_object(ctruuid)
    
    procedures = []
    for prcuuid in controller.object["procedures"]:
        procedures.append(collection.get_object(prcuuid).object)
    
    hstuuids = []
    grpuuids = []
    
    for hstuuid in controller.object["hosts"]:
        get_hosts(hstuuid, hstuuids, grpuuids, collection)
    
    hosts = []
    for hstuuid in hstuuids:
        host = collection.get_object(hstuuid)
        hosts.append(collection.get_object(hstuuid).object)
    
    return {"hosts" : hosts, "procedures" : procedures}
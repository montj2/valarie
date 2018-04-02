#!/usr/bin/python
################################################################################
# TASK
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/30/2016 Original construction
# 06/06/2017 Optimized JSON responses
################################################################################

import traceback

from .document import Collection
from .ramdocument import Collection as RAMCollection
from ..controller.messaging import add_message
#from .eventlog import create_task_execute_event

from imp import new_module
from time import time

class TaskError:
    def __init__(self, uuid):
        self.output = ['<font color="red">'] + traceback.format_exc().split("\n") + ["</font>"]
        self.uuid = uuid
        self.status = 5 

    def execute(self, cli):
        return self.status

def execute(tskuuid, hstuuid, session):
    inventory = Collection("inventory")
    results = RAMCollection("results")
    
    for result in results.find(hstuuid = hstuuid, tskuuid = tskuuid):
        result.destroy()
    
    result = results.get_object()
    
    result.object['start'] = time()
        
    status_code_body = ""
    status_data = {}
    
    for status in inventory.find(type = "status"):
        try:
            status_code_body += "{0}=int('{1}')\n".format(status.object["alias"], status.object["code"])
            status_data[int(status.object["code"])] = status.object
        except Exception:
            add_message(traceback.format_exc())
    
    host = inventory.get_object(hstuuid)
    result.object['host'] = {}
    result.object['host']['host'] = host.object['host']
    result.object['host']['name'] = host.object['name']
    result.object['host']['objuuid'] = hstuuid
    
    #create_task_execute_event(session, inventory.get_object(tskuuid), host)
    
    tempmodule = new_module("tempmodule")
    
    try:
        exec inventory.get_object(host.object["console"]).object["body"] in tempmodule.__dict__
        cli = tempmodule.Console(session = session, host = host.object)
        
        try:
            inv_task = inventory.get_object(tskuuid)
            
            result.object['task'] = {}
            result.object['task']["name"] = inv_task.object["name"]
            result.object['task']["start"] = None
            result.object['task']["stop"] = None
            result.object['task']["tskuuid"] = tskuuid
            
            inv_task.object["body"] in tempmodule.__dict__
            exec inv_task.object["body"] + "\n" + status_code_body in tempmodule.__dict__
            task = tempmodule.Task()
            
            try:
                task.execute(cli)
            except Exception:
                task = TaskError(tskuuid)
                add_message(traceback.format_exc())
        except Exception:
            task = TaskError(tskuuid)
            add_message(traceback.format_exc())
    except Exception:
        task = TaskError(tskuuid)
        add_message(traceback.format_exc())
        
    result.object['output'] = task.output
    
    try:
        result.object['status'] = status_data[task.status]
        
        result.object['status'] = {}
        result.object['status']["name"] = status_data[task.status]["name"]
        result.object['status']["code"] = status_data[task.status]["code"]
        result.object['status']["abbreviation"] = status_data[task.status]["abbreviation"]
        result.object['status']["cfg"] = status_data[task.status]["cfg"]
        result.object['status']["cbg"] = status_data[task.status]["cbg"]
        result.object['status']["sfg"] = status_data[task.status]["sfg"]
        result.object['status']["sbg"] = status_data[task.status]["sbg"]
    except Exception:
        add_message(traceback.format_exc())
        result.object['status'] = {"code" : task.status}
        
    result.object['stop'] = time()
        
    #for line in dir(tempmodule):
    #    print "module: ", line
    
    result.set()
    
    return result.object

def get_host_grid(tskuuid):
    collection = Collection("inventory")
    
    task = collection.get_object(tskuuid)
    
    grid_data = []
    
    for hstuuid in task.object["hosts"]:
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
                        c.destroy()
                        host.object["hosts"].remove(uuid)
                        host.set()
                
                grid_data.append({"type" : host.object["type"], \
                                  "name" : host.object["name"], \
                                  "host" : str("<br>").join(hosts), \
                                  "objuuid" : host.object["objuuid"]})
        else:
            add_message("host {0} is missing!".format(hstuuid))
            #grid_data.append({"name" : "MISSING!", "host" : "?.?.?.?", "objuuid" : hstuuid})
            host.destroy()
            task.object["hosts"].remove(hstuuid)
            task.set()
        
    return grid_data
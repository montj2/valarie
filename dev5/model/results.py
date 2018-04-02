#!/usr/bin/python
################################################################################
# RESULTS
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 12/05/2016 Original construction
# 06/05/2017 Replaced sleep with timer object
################################################################################

import traceback

from threading import Thread, Timer
from time import time

from .ramdocument import Collection as RAMCollection
from .document import Collection
from .utils import sucky_uuid

def delete(objuuid):
    collection = RAMCollection("results")
    collection.get_object(objuuid).destroy()

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
    
def get_controller_results(ctruuid):
    results = RAMCollection("results")
    
    collection = Collection("inventory")
    
    controller = collection.get_object(ctruuid)
    
    controller_results = []
    
    hstuuids = []
    grpuuids = []
    for hstuuid in controller.object["hosts"]:
        get_hosts(hstuuid, hstuuids, grpuuids, collection)
    
    for hstuuid in hstuuids:
        for prcuuid in controller.object["procedures"]:
            try:
                result = results.find(hstuuid = hstuuid, prcuuid = prcuuid)[0].object
                
                if result["start"] != None and result["stop"] != None:
                    result["duration"] = result["stop"] - result["start"]
                elif result["start"] != None:
                    result["duration"] = time() - result["start"]
                else:
                    result["duration"] = 0
                
                if result["stop"] == None:
                    result["age"] = 0
                else:
                    result["age"] = time() - result["stop"]
                    
                controller_results.append(result)
            except IndexError:
                pass
    
    return controller_results

def get_procedure_result(prcuuid, hstuuid):
    collection = Collection("inventory")
    
    results = RAMCollection("results")
    
    result_objects = []
    
    host = collection.get_object(hstuuid)
        
    hstuuids = []
    grpuuids = []
    get_hosts(hstuuid, hstuuids, grpuuids, collection)

    for hstuuid in hstuuids:
        try:
            result = results.find(hstuuid = hstuuid, prcuuid = prcuuid)[0].object
            
            if result["start"] != None and result["stop"] != None:
                result["duration"] = result["stop"] - result["start"]
            elif result["start"] != None:
                result["duration"] = time() - result["start"]
            else:
                result["duration"] = 0
            
            result_objects.append(result)
        except IndexError:
            pass
    
    return result_objects
    

def worker():
    Timer(3600, worker).start()
    
    results = RAMCollection("results")
    
    for objuuid in results.list_objuuids():
        result = results.get_object(objuuid)
        
        try:
            if time() - result.object["start"] > 28800:
                result.destroy()
        except Exception:
            result.destroy()
    
collection = RAMCollection("results")
collection.create_attribute("start", "['start']")
collection.create_attribute("stop", "['stop']")
collection.create_attribute("tskuuid", "['task']['objuuid']")
collection.create_attribute("prcuuid", "['procedure']['objuuid']")
collection.create_attribute("hstuuid", "['host']['objuuid']")

Thread(target = worker).start()
#!/usr/bin/python
################################################################################
# PROCEDURE
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/22/2016 Original construction
# 06/05/2017 Replaced sleep with timer object
# 06/06/2017 Optimized JSON responses
################################################################################

MAX_JOBS = 10
MAX_JOBS_PER_HOST = 2

import traceback

from threading import Lock, Thread, Timer
from time import time
from imp import new_module

from .document import Collection
from .ramdocument import Collection as RAMCollection
from .utils import sucky_uuid
from ..controller.flags import touch_flag
from ..controller.messaging import add_message
#from .eventlog import create_procedure_execute_event, \
#                      create_task_execute_event

global global_jobs
global global_jobs_lock
global_jobs = {}
global_job_lock = Lock()

def get_task_grid(prcuuid):
    collection = Collection("inventory")
    
    procedure = collection.get_object(prcuuid)
    
    grid_data = []
    
    for tskuuid in procedure.object["tasks"]:
        task = collection.get_object(tskuuid)
        
        if "type" in task.object:
            grid_data.append({"name" : task.object["name"], "objuuid" : task.object["objuuid"]})
        else:
            add_message("task {0} is missing!".format(tskuuid))
            grid_data.append({"name" : "MISSING!", "objuuid" : tskuuid})
        
    return grid_data

def get_host_grid(prcuuid):
    collection = Collection("inventory")
    
    procedure = collection.get_object(prcuuid)
    
    grid_data = []
    
    for hstuuid in procedure.object["hosts"]:
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
            procedure.object["hosts"].remove(hstuuid)
            procedure.set()
        
    return grid_data

def update_job(jobuuid, key, value):
    global_job_lock.acquire()
    global_jobs[jobuuid][key] = value
    global_job_lock.release()
    touch_flag("queueState")
    
def set_job(jobuuid, value):
    global_job_lock.acquire()
    global_jobs[jobuuid] = value
    global_job_lock.release()
    touch_flag("queueState")
    
def get_job(jobuuid):
    try:
        global_job_lock.acquire()
        global_jobs[jobuuid]
    except KeyError:
        global_jobs[jobuuid] = None
    finally:
        global_job_lock.release()
        return global_jobs[jobuuid]

def del_job(jobuuid):
    try:
        global_job_lock.acquire()
        del global_jobs[jobuuid]
    except KeyError:
        pass
    finally:
        touch_flag("queueState")
        global_job_lock.release()

        
def worker():
    Timer(1, worker).start()
    
    global_job_lock.acquire()
    
    running_jobs_count = 0
    
    try:    
        running_jobs_counts = {}
        for key in global_jobs.keys():
            running_jobs_counts[global_jobs[key]["host"]["objuuid"]] = 0
            
        for key in global_jobs.keys():
            if global_jobs[key]["process"] != None:
                if global_jobs[key]["process"].is_alive():
                    running_jobs_count += 1
                    running_jobs_counts[global_jobs[key]["host"]["objuuid"]] += 1
                else:
                    del global_jobs[key]
                    touch_flag("queueState")
            
        for key in global_jobs.keys():
            if running_jobs_count < MAX_JOBS:
                if global_jobs[key]["process"] == None:
                    if running_jobs_counts[global_jobs[key]["host"]["objuuid"]] < MAX_JOBS_PER_HOST:
                        global_jobs[key]["process"] = Thread(target = run_procedure, \
                                                            args = (global_jobs[key]["host"]["objuuid"], \
                                                                    global_jobs[key]["procedure"]["objuuid"], \
                                                                    global_jobs[key]["session"], \
                                                                    global_jobs[key]["jobuuid"]))
                        global_jobs[key]["start time"] = time()
                        global_jobs[key]["process"].start()
                        running_jobs_count += 1
                        running_jobs_counts[global_jobs[key]["host"]["objuuid"]] += 1
                        touch_flag("queueState")
    except Exception:
        add_message("queue exception\n{0}".format(traceback.format_exc()))

    global_job_lock.release()

def get_jobs_grid():
    grid_data = []
    global_job_lock.acquire()
    
    for jobuuid, dict in global_jobs.iteritems():
        row = {}
        row["name"] = dict["procedure"]["name"]
        row["host"] = dict["host"]["name"]
        row["progress"] = dict["progress"]
        grid_data.append(row)
    
    global_job_lock.release()
    
    for i in range(0, len(grid_data)):
        for j in range(i, len(grid_data)):
            if grid_data[i]["progress"] < grid_data[j]["progress"]:
                grid_data[i], grid_data[j] = grid_data[j], grid_data[i]
    
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
    
def queue_procedure(hstuuid, prcuuid, session):
    inventory = Collection("inventory")
    
    procedure = inventory.get_object(prcuuid)
    
    hstuuids = []
    grpuuids = []
    get_hosts(hstuuid, hstuuids, grpuuids, inventory)
    
    for hstuuid in hstuuids:
        add_message("Queued host: {0}, procedure {1}...".format(hstuuid, prcuuid))
        
        host = inventory.get_object(hstuuid)
        if host.object["type"] == "host":
            jobuuid = sucky_uuid()
            
            job = {
                "jobuuid" : jobuuid,
                "host" : host.object,
                "procedure" : procedure.object,
                "session" : session,
                "process" : None,
                "queue time" : time(),
                "start time" : None,
                "progress" : 0,
            }
        
            set_job(jobuuid, job)
    
class TaskError:
    def __init__(self, uuid):
        self.output = ['<font color="red">'] + traceback.format_exc().split("\n") + ["</font>"]
        self.uuid = uuid
        self.status = 5 

    def execute(self, cli):
        return self.status
    
def run_procedure(hstuuid, prcuuid, session, jobuuid = None):
    add_message("Executing host: {0}, procedure {1}...".format(hstuuid, prcuuid))
    
    inventory = Collection("inventory")
    results = RAMCollection("results")
    
    for result in results.find(hstuuid = hstuuid, prcuuid = prcuuid):
        result.destroy()
    
    result = results.get_object()
    
    result.object['start'] = time()
    result.object["output"] = []
    
    status_code_body = ""
    status_data = {}
    
    result.object["output"].append("importing status codes...")
    
    for status in inventory.find(type = "status"):
        try:
            status_code_body += "{0}=int('{1}')\n".format(status.object["alias"], status.object["code"])
            status_data[int(status.object["code"])] = status.object
        except Exception:
            result.object["output"] += traceback.format_exc().split("\n")
    
    host = inventory.get_object(hstuuid)
    result.object['host'] = {}
    result.object['host']['host'] = host.object['host']
    result.object['host']['name'] = host.object['name']
    result.object['host']['objuuid'] = hstuuid
    
    #create_procedure_execute_event(session, inventory.get_object(prcuuid), host)    
    
    tempmodule = new_module("tempmodule")
    
    winning_status = None
    continue_procedure = True
    
    result.object["tasks"] = []
    
    procedure = inventory.get_object(prcuuid)
    result.object['procedure'] = {}
    result.object['procedure']['name'] = procedure.object['name']
    result.object['procedure']['title'] = procedure.object['title']
    result.object['procedure']['description'] = procedure.object['description']
    result.object['procedure']['objuuid'] = prcuuid
    
    result.object['rfcs'] = []
    for rfcuuid in procedure.object["rfcs"]:
        result.object['rfcs'].append(inventory.get_object(rfcuuid).object)
    
    try:
        tskuuids = procedure.object["tasks"]
    except Exception:
        add_message(traceback.format_exc())
        
    try:
        for seq_num, tskuuid in enumerate(tskuuids):
            task_result = {}
            task_result["name"] = inventory.get_object(tskuuid).object["name"]
            task_result["start"] = None
            task_result["stop"] = None
            task_result["tskuuid"] = tskuuid
            
            try:
                exec inventory.get_object(tskuuid).object["body"] + "\n" + status_code_body in tempmodule.__dict__
                task = tempmodule.Task()
            except Exception:
                task = TaskError(tskuuid)
            
            task_result["output"] = task.output
            try:
                task_result["status"] = {}
                task_result["status"]["name"] = status_data[task.status]["name"]
                task_result["status"]["code"] = status_data[task.status]["code"]
                task_result["status"]["abbreviation"] = status_data[task.status]["abbreviation"]
                task_result["status"]["cfg"] = status_data[task.status]["cfg"]
                task_result["status"]["cbg"] = status_data[task.status]["cbg"]
                task_result["status"]["sfg"] = status_data[task.status]["sfg"]
                task_result["status"]["sbg"] = status_data[task.status]["sbg"]
            except Exception:
                task_result['status'] = {"code" : task.status}
            
            result.object['tasks'].append(task_result)
        
        result.object['status'] = {
            "name" : "Executing",
            "code" : 0,
            "abbreviation" : "EXEC",
            "cfg" : "000000",
            "cbg" : "FFFFFF",
            "sfg" : "000000",
            "sbg" : "999999"
        }
        
        result.object['stop'] = None
        result.set()
        touch_flag("results")
    except Exception:
        add_message(traceback.format_exc())
    
    procedure_status = None
    
    try:
        try:
            result.object["output"].append("importing console...")
            exec inventory.get_object(host.object["console"]).object["body"] in tempmodule.__dict__
            cli = tempmodule.Console(session = session, host = host.object)
        except Exception:
            result.object["output"] += traceback.format_exc().split("\n")
        
        for seq_num, tskuuid in enumerate(tskuuids):
            task_result = {}
            task_result["name"] = inventory.get_object(tskuuid).object["name"]
            task_result["start"] = None
            task_result["stop"] = None
            
            try:
                exec inventory.get_object(tskuuid).object["body"] + "\n" + status_code_body in tempmodule.__dict__
                task = tempmodule.Task()
                
                if continue_procedure:
                    task_result["start"] = time()
                    
                    try:
                        task.execute(cli)
                    except Exception:
                        task = TaskError(tskuuid)
                    
                    task_result["stop"] = time()
                    
                    #create_task_execute_event(session, inventory.get_object(tskuuid), host)
            except Exception:
                task = TaskError(tskuuid)
                result.object["output"] += traceback.format_exc().split("\n")
            
            task_result["output"] = task.output
            try:
                task_result["output"] = task.output
            
                task_result["status"] = {}
                task_result["status"]["name"] = status_data[task.status]["name"]
                task_result["status"]["code"] = status_data[task.status]["code"]
                task_result["status"]["abbreviation"] = status_data[task.status]["abbreviation"]
                task_result["status"]["cfg"] = status_data[task.status]["cfg"]
                task_result["status"]["cbg"] = status_data[task.status]["cbg"]
                task_result["status"]["sfg"] = status_data[task.status]["sfg"]
                task_result["status"]["sbg"] = status_data[task.status]["sbg"]
            
                try:
                    continue_flag = procedure.object["continue {0}".format(task.status)]
                    
                    if continue_flag == 'false':
                        continue_flag = False
                    
                    if not continue_flag:
                        continue_procedure = False
                except Exception:
                    continue_procedure = False
            except Exception:
                task_result['status'] = {"code" : task.status}
                continue_procedure = False
                
            result.object['tasks'][seq_num] = task_result
            
            if winning_status == None:
                winning_status = task.status
                procedure_status = task_result['status']
            elif task.status < winning_status:
                winning_status = task.status
                procedure_status = task_result['status']
            
            if jobuuid:
                update_job(jobuuid, "progress", float(seq_num + 1) / float(len(tskuuids)))
            
            result.object['stop'] = time()
            result.set()
            touch_flag("results")
        
        if procedure_status != None:
            result.object['status'] = procedure_status
            result.set()
            touch_flag("results")
    except Exception:
        add_message(traceback.format_exc())
    
    return result.object

Thread(target = worker).start()
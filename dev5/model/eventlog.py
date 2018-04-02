#!/usr/bin/python
################################################################################
# EVENT LOG
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 04/24/2017 Original construction
################################################################################

import traceback

from threading import Thread, Timer
from time import time, strftime, localtime

from .document import Collection


def create_logon_event(user):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "type" : "logon"
    }
    event.set()
    return event

def create_logon_failure_event(message):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "message" : message,
        "type" : "logon failure"
    }
    event.set()
    return event
    
def create_logout_event(user):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "type" : "logout"
    }
    event.set()
    return event

def create_user_create_event(user, target_user):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "target user" : target_user.object,
        "type" : "create user"
    }
    event.set()
    return event

def create_user_delete_event(user, target_user):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "target user" : target_user.object,
        "type" : "delete user"
    }
    event.set()
    return event

def create_inventory_move_event(user, inventory):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "inventory object" : inventory.object,
        "type" : "inventory move"
    }
    event.set()
    return event

def create_inventory_copy_event(user, inventory):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "inventory object" : inventory.object,
        "type" : "inventory copy"
    }
    event.set()
    return event

def create_inventory_create_event(user, inventory):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "inventory object" : inventory.object,
        "type" : "inventory create"
    }
    event.set()
    return event

def create_inventory_delete_event(user, inventory):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "inventory object" : inventory.object,
        "type" : "inventory delete"
    }
    event.set()
    return event

def create_inventory_export_event(user, objuuids):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "objuuids" : objuuids,
        "type" : "inventory export"
    }
    event.set()
    return event

def create_inventory_import_event(user, objuuids):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "objuuids" : objuuids,
        "type" : "inventory import"
    }
    event.set()
    return event

def create_procedure_execute_event(session, procedure, host):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : session,
        "procedure" : procedure.object,
        "host" : host.object,
        "type" : "execute procedure"
    }
    event.set()
    return event

def create_task_execute_event(session, task, host):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : session,
        "task" : task.object,
        "host" : host.object,
        "type" : "execute task"
    }
    event.set()
    return event

def create_terminal_event(user, host):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "host" : host.object,
        "type" : "terminal create"
    }
    event.set()
    return event

def create_schedule_event(schedule):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "schedule" : schedule.object,
        "type" : "execute schedule"
    }
    event.set()
    return event
    
def create_terminal_upload_event(user, filename):
    collection = Collection("events")
    event = collection.get_object()
    event.object = {
        "timestamp" : time(),
        "user" : user.object,
        "filename" : filename,
        "type" : "terminal upload"
    }
    event.set()
    return event

def get_events_str(max_age = None):
    output = ""
    
    events = Collection("events")
    
    if max_age == None:
        for evtuuid in events.list_objuuids():
            output += get_event_str(events.get_object(evtuuid)) + "\n"
    else:
        for evtuuid in events.list_objuuids():
            event = events.get_object(evtuuid)
            if event.object["timestamp"] > time() - int(max_age):
                output += get_event_str(event) + "\n"
    
    return output

def get_event_str(event):
    output = ""
    
    output += "Event UUID: {0}\n".format(event.object["objuuid"])
        
    output += "Event Type: {0}\n".format(event.object["type"])
       
    output += "Timestamp: {0}\n".format(strftime('%Y-%m-%d %H:%M:%S', localtime(event.object["timestamp"])))
        
    if "schedule" in event.object:
        try:
            output += "Schedule: {0} {1}\n".format(event.object["schedule"]["objuuid"], \
                                                       event.object["schedule"]["name"])
        except Exception:
            output += "Schedule: {0}\n".format(traceback.format_exc())
        
    if "user" in event.object:
        try:
            output += "User: {0} {1} {2}\n".format(event.object["user"]["name"], \
                                                   event.object["user"]["first name"], \
                                                   event.object["user"]["last name"])
        except Exception:
            output += "User: {0}\n".format(traceback.format_exc())
        
    if "message" in event.object:
        output += "Message: {0}\n".format(event.object["message"])
        
    if "filename" in event.object:
        output += "Filename: {0}\n".format(event.object["filename"])
        
    if "host" in event.object:
        try:
            output += "Host: {0} {1} {2}\n".format(event.object["host"]["objuuid"], \
                                                   event.object["host"]["name"], \
                                                   event.object["host"]["host"])
        except Exception:
            output += "Host: {0}\n".format(traceback.format_exc())
        
    if "procedure" in event.object:
        try:
            output += "Procedure: {0} {1}\n".format(event.object["procedure"]["objuuid"], \
                                                    event.object["procedure"]["name"])
        except Exception:
            output += "Procedure: {0}\n".format(traceback.format_exc())
        
    if "task" in event.object:
        try:
            output += "Task: {0} {1}\n".format(event.object["task"]["objuuid"], \
                                               event.object["task"]["name"])
        except Exception:
            output += "Task: {0}\n".format(traceback.format_exc())
    
    return output

    
def delete(objuuid):
    collection = Collection("events")
    collection.get_object(objuuid).destroy()

def worker():
    events = Collection("events")
    
    for objuuid in events.list_objuuids():
        event = events.get_object(objuuid)
        
        try:
            if time() - event.object["timestamp"] > 604800:
                event.destroy()
        except Exception:
            event.destroy()
    
    Timer(3600.0, worker).start()

collection = Collection("events")
collection.create_attribute("timestamp", "['timestamp']")
collection.create_attribute("username", "['user']['name']")
collection.create_attribute("type", "['type']")
"""
collection.create_attribute("start", "['start']")
collection.create_attribute("stop", "['stop']")
collection.create_attribute("tskuuid", "['task']['objuuid']")
collection.create_attribute("prcuuid", "['procedure']['objuuid']")
collection.create_attribute("hstuuid", "['host']['objuuid']")
"""
Thread(target = worker).start()
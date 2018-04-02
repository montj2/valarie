#!/usr/bin/python
################################################################################
# SCHEDULE
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 04/24/2017 Original construction
################################################################################

import traceback

from datetime import datetime
from threading import Thread, Timer
from time import time, sleep
from imp import new_module

from .eventlog import create_schedule_event
from .document import Collection
from ..controller.messaging import add_message

def eval_cron_field(cron_str, now_val):
    result = False
    
    try:
        for field in cron_str.split(','):
            if '*' in field:
                result = True
            elif '-' in field:
                if int(now_val) in range(int(field.split('-')[0]), \
                                         int(field.split('-')[1]) + 1):
                    result = True
            elif int(field) == int(now_val):
                result = True
    except Exception:
        add_message("schedule exception\n{0}".format(traceback.format_exc()))
    
    return result

def worker():
    Timer(60.0, worker).start()
    
    now = datetime.now()
    
    inventory = Collection("inventory")
        
    for schedule in inventory.find(type = "schedule"):
        try:
            if schedule.object["enabled"] == True or \
               schedule.object["enabled"] == "true":
                if eval_cron_field(schedule.object["minutes"], now.minute) and \
                   eval_cron_field(schedule.object["hours"], now.hour) and \
                   eval_cron_field(schedule.object["dayofmonth"], now.day) and \
                   eval_cron_field(schedule.object["dayofweek"], now.weekday()) and \
                   eval_cron_field(schedule.object["year"], now.year):
                    Thread(target = run_schedule, args = (schedule.objuuid,)).start()
        except Exception:
            add_message("schedule exception\n{0}".format(traceback.format_exc()))

def run_schedule(schuuid):
    add_message("Executing schedule: {0}...".format(schuuid))
    
    inventory = Collection("inventory")
    
    schedule = inventory.get_object(schuuid)
    
    #create_schedule_event(schedule)
    
    tempmodule = new_module("tempmodule")
    
    try:
        exec schedule.object["body"] in tempmodule.__dict__
    except Exception:
        add_message("schedule exception\n{0}".format(traceback.format_exc()))
    
Thread(target = worker).start()
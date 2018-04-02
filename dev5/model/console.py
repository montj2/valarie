#!/usr/bin/python
################################################################################
# CONSOLE
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/28/2016 Original construction
################################################################################

from .document import Collection

def get_consoles():
    collection = Collection("inventory")
    
    console_objects = []
    
    for object in collection.find(type = "console"):
        console_objects.append(object.object)
        
    return console_objects
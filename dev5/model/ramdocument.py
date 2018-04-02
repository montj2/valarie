#!/usr/bin/python
################################################################################
# DOCUMENT
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 12/23/2016 Original construction
# 06/06/2017 Fixed bug with object setting and index refreshing
################################################################################

import pickle
import traceback

from threading import Lock

from .utils import sucky_uuid

global RAM_DOCUMENT_LOCK
RAM_DOCUMENT_LOCK = Lock()

global RAM_DOCUMENT
RAM_DOCUMENT = {}

class Document:
    def __init__(self):
        RAM_DOCUMENT_LOCK.acquire()
        
        if "TBL_JSON_COL" not in RAM_DOCUMENT:
            RAM_DOCUMENT["TBL_JSON_COL"] = {}
        
        if "TBL_JSON_OBJ" not in RAM_DOCUMENT:
            RAM_DOCUMENT["TBL_JSON_OBJ"] = {}
        
        if "TBL_JSON_ATTR" not in RAM_DOCUMENT:
            RAM_DOCUMENT["TBL_JSON_ATTR"] = {}
        
        if "TBL_JSON_IDX" not in RAM_DOCUMENT:
            RAM_DOCUMENT["TBL_JSON_IDX"] = {}
        
        RAM_DOCUMENT_LOCK.release()
    
    def create_object(self, coluuid, objuuid):
        try:
            RAM_DOCUMENT_LOCK.acquire()
            
            RAM_DOCUMENT["TBL_JSON_OBJ"]["-".join([coluuid, objuuid])] = pickle.dumps({"objuuid" : objuuid, "coluuid" : coluuid})
            
        except Exception:
            print traceback.format_exc()
        finally:
            RAM_DOCUMENT_LOCK.release()
    
    def set_object(self, coluuid, objuuid, object):
        try:
            RAM_DOCUMENT_LOCK.acquire()
            object["objuuid"] = objuuid
            object["coluuid"] = coluuid
            
            RAM_DOCUMENT["TBL_JSON_OBJ"]["-".join([coluuid, objuuid])] = pickle.dumps(object)
            
            keys = []
            for key, value in RAM_DOCUMENT["TBL_JSON_IDX"].iteritems():
                if objuuid in key:
                    keys.append(key)
            
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_IDX"][key]

            attributes = {}
            for key, value in RAM_DOCUMENT["TBL_JSON_ATTR"].iteritems():
                if value["coluuid"] == coluuid:
                    attributes[RAM_DOCUMENT["TBL_JSON_ATTR"][key]["attribute_name"]] = RAM_DOCUMENT["TBL_JSON_ATTR"][key]["path"]
                
            for attribute_name in attributes:
                try:
                    RAM_DOCUMENT["TBL_JSON_IDX"]["-".join([coluuid, objuuid, attribute_name])] = {"coluuid" : coluuid, "attribute_name" : attribute_name, "objuuid" : objuuid, "value" : str(eval("str(self.get_object_no_lock(objuuid)" + attributes[attribute_name] + ")"))}
                except Exception:
                    #print traceback.format_exc()
                    pass
        except Exception:
            print traceback.format_exc()
        finally:
            RAM_DOCUMENT_LOCK.release()
    
    def get_object_no_lock(self, objuuid):
        for key, value in RAM_DOCUMENT["TBL_JSON_OBJ"].iteritems():
            if objuuid in key:
                return pickle.loads(value)
        
        raise IndexError, "OBJUUID not found!"
    
    def get_object(self, objuuid):
        RAM_DOCUMENT_LOCK.acquire()
        
        for key, value in RAM_DOCUMENT["TBL_JSON_OBJ"].iteritems():
            if objuuid in key:
                RAM_DOCUMENT_LOCK.release()
                return pickle.loads(value)
        
        RAM_DOCUMENT_LOCK.release()
        raise IndexError, "OBJUUID not found!"
    
    def find_objects(self, coluuid, attribute, value):
        RAM_DOCUMENT_LOCK.acquire()
        
        objuuids = []
        for key, index in RAM_DOCUMENT["TBL_JSON_IDX"].iteritems():
            if index["value"] == value and \
               index["coluuid"] == coluuid and \
               index["attribute_name"] == attribute:
                objuuids.append(index["objuuid"])
        
        RAM_DOCUMENT_LOCK.release()
        
        return objuuids
    
    def delete_object(self, objuuid):
        try:
            RAM_DOCUMENT_LOCK.acquire()
            
            keys = []
            for key, value in RAM_DOCUMENT["TBL_JSON_OBJ"].iteritems():
                if objuuid in key:
                    keys.append(key)
            
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_OBJ"][key]
            
            keys = []
            for key, value in RAM_DOCUMENT["TBL_JSON_IDX"].iteritems():
                if objuuid in key:
                    keys.append(key)
            
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_IDX"][key]
        except Exception:
            print traceback.format_exc()
        finally:
            RAM_DOCUMENT_LOCK.release()
    
    def create_attribute(self, coluuid, attribute, path):
        try:
            RAM_DOCUMENT_LOCK.acquire()
            
            RAM_DOCUMENT["TBL_JSON_ATTR"]["-".join([coluuid, attribute])] = {"path" : path, "attribute_name" : attribute, "coluuid" : coluuid}
            
            for key, value in RAM_DOCUMENT["TBL_JSON_IDX"].iteritems():
                if value["attribute_name"] == attribute:
                    del RAM_DOCUMENT["TBL_JSON_IDX"][key]
        
            objects = {}
            for key, value in RAM_DOCUMENT["TBL_JSON_OBJ"].iteritems():
                if coluuid in key:
                    object = pickle.loads(RAM_DOCUMENT["TBL_JSON_OBJ"][key])
                    objects[object["objuuid"]] = object
            
            for objuuid in objects:
                try:
                    RAM_DOCUMENT["TBL_JSON_IDX"]["-".join([coluuid, objuuid, attribute])] = {"coluuid" : coluuid, "attribute_name" : attribute, "objuuid" : objuuid, "value" : str(eval("str(objects[objuuid]" + path + ")"))}
                except Exception:
                    traceback.format_exc()
        
        except Exception:
            print traceback.format_exc()
        finally:
            RAM_DOCUMENT_LOCK.release()
    
    def delete_attribute(self, coluuid, attribute):
        try:
            RAM_DOCUMENT_LOCK.acquire()
            
            keys = []
            
            for key, value in RAM_DOCUMENT["TBL_JSON_ATTR"].iteritems():
                if value["attribute_name"] == attribute and value["coluuid"] == coluuid:
                    keys.append(key)
            
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_ATTR"][key]
            
            keys = []
            for key, value in RAM_DOCUMENT["TBL_JSON_IDX"].iteritems():
                if value["attribute_name"] == attribute and value["coluuid"] == coluuid:
                    keys.append(key)
            
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_IDX"][key]
        except Exception:
            print traceback.format_exc()
        finally:
            RAM_DOCUMENT_LOCK.release()
        
    def list_attributes(self, coluuid):
        RAM_DOCUMENT_LOCK.acquire()
        
        attributes = {}
        for key, value in RAM_DOCUMENT["TBL_JSON_ATTR"].iteritems():
            if value["coluuid"] == coluuid:
                attributes[RAM_DOCUMENT["TBL_JSON_ATTR"][key]["attribute_name"]] = RAM_DOCUMENT["TBL_JSON_ATTR"][key]["path"]
        
        RAM_DOCUMENT_LOCK.release()
        
        return attributes
    
    def create_collection(self, uuid = None, name = "New Collection"):
        RAM_DOCUMENT_LOCK.acquire()

        if not uuid:
            uuid = sucky_uuid()
            
        RAM_DOCUMENT["TBL_JSON_COL"][uuid] = name

        RAM_DOCUMENT_LOCK.release()

        return uuid
    
    def delete_collection(self, uuid):
        try:
            RAM_DOCUMENT_LOCK.acquire()
            
            del RAM_DOCUMENT["TBL_JSON_COL"][uuid]
            
            keys = []
            for key in RAM_DOCUMENT["TBL_JSON_OBJ"]:
                if uuid in key:
                    keys.append(key)
            
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_OBJ"][key]
            
            keys = []
            for key in RAM_DOCUMENT["TBL_JSON_ATTR"]:
                if uuid in key:
                    keys.append(key)
                    
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_ATTR"][key]
            
            keys = []
            for key in RAM_DOCUMENT["TBL_JSON_IDX"]:
                if uuid in key:
                    keys.append(key)
            
            for key in keys:
                del RAM_DOCUMENT["TBL_JSON_IDX"][key]
        except Exception:
            print traceback.format_exc()
        finally:
            RAM_DOCUMENT_LOCK.release()
    
    def rename_collection(self, uuid, name):
        RAM_DOCUMENT_LOCK.acquire()
        RAM_DOCUMENT["TBL_JSON_COL"][uuid] = name
        RAM_DOCUMENT_LOCK.release()
    
    def list_collections(self):
        RAM_DOCUMENT_LOCK.acquire()
        
        collections = {}
        for key, value in RAM_DOCUMENT["TBL_JSON_COL"].iteritems():
            collections[value] = key
        
        RAM_DOCUMENT_LOCK.release()
        
        return collections
    
    def list_collection_objects(self, coluuid):
        try:
            RAM_DOCUMENT_LOCK.acquire()
            
            objuuids = []
            for key, value in RAM_DOCUMENT["TBL_JSON_OBJ"].iteritems():
                if coluuid in key:
                    objuuids.append(pickle.loads(value)["objuuid"])
        except Exception:
            print traceback.format_exc()
        finally:
            RAM_DOCUMENT_LOCK.release()
        
        return objuuids

class Object(Document):
    def __init__(self, coluuid, objuuid):
        Document.__init__(self)
        
        self.objuuid = objuuid
        self.coluuid = coluuid
        self.load()
    
    def load(self):
        try:
            self.object = Document.get_object(self, self.objuuid)
        except IndexError:
            Document.create_object(self, self.coluuid, self.objuuid)
            self.object = Document.get_object(self, self.objuuid)
    
    def set(self):
        Document.set_object(self, self.coluuid, self.objuuid, self.object)
    
    def destroy(self):
        Document.delete_object(self, self.objuuid)
        self.object = None

class Collection(Document):
    def __init__(self, collection_name):
        Document.__init__(self)
        self.collection_name = collection_name
        
        try:
            self.coluuid = Document.list_collections(self)[self.collection_name]
        except KeyError:
            self.coluuid = Document.create_collection(self, name = self.collection_name)

    def destroy(self):
        Document.delete_collection(self, self.coluuid)
    
    def rename(self, name):
        Document.rename_collection(self, self.coluuid, name)
        self.collection_name = name
    
    def create_attribute(self, attribute, path):
        Document.create_attribute(self, self.coluuid, attribute, path)
    
    def delete_attribute(self, attribute):
        Document.delete_attribute(self, self.coluuid, attribute)
    
    def find(self, **kargs):
        objuuid_sets = []
        for attribute, value in kargs.iteritems():
            objuuid_sets.append(Document.find_objects(self, self.coluuid, attribute, value))
        
        intersection = set(objuuid_sets[0])
        for objuuids in objuuid_sets[1:]:
            intersection = intersection.intersection(set(objuuids))
        
        objects = []
        for objuuid in list(intersection):
            objects.append(Object(self.coluuid, objuuid))
        
        return objects
    
    def find_objuuids(self, **kargs):
        objuuid_sets = []
        for attribute, value in kargs.iteritems():
            objuuid_sets.append(Document.find_objects(self, self.coluuid, attribute, value))
        
        intersection = set(objuuid_sets[0])
        for objuuids in objuuid_sets[1:]:
            intersection = intersection.intersection(set(objuuids))
        
        objuuids = []
        for objuuid in list(intersection):
            objuuids.append(objuuid)
        
        return objuuids

    def get_object(self, objuuid = None):
        if not objuuid:
            objuuid = sucky_uuid()
        return Object(self.coluuid, objuuid)
    
    def list_objuuids(self):
        return Document.list_collection_objects(self, self.coluuid)
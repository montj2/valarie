#!/usr/bin/python
################################################################################
# DOCUMENT
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 11/01/2016 Original construction
# 12/02/2016 Combined set and index methods in the document class
#            Added mutex lock to set to resolve sqlite deadlocking
# 12/05/2016 Added try statements to all mutating document methods
# 12/06/2016 Added commits to finally blocks
# 05/01/2017 Fixed bug with create attribute method. All collections and indexes
#              with matching attribute names were being affected.
# 06/19/2017 Removed UTF decoder from AES cipher.
# 11/24/2017 Added automatic vacuuming.
################################################################################

import sqlite3
import pickle
import traceback
import base64
import hashlib

from Crypto import Random
from Crypto.Cipher import AES
from threading import Lock, Timer
from .utils import sucky_uuid

global DOCUMENT_LOCK
DOCUMENT_LOCK = Lock()

class AESCipher(object):
    def __init__(self, key): 
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

class Document:
    def __init__(self):
        self.cipher = AESCipher("this is the key")
        
        DOCUMENT_LOCK.acquire()
        
        self.connection = sqlite3.connect("db.sqlite", 300)
        self.cursor = self.connection.cursor()

        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_COL (
                               COLUUID VARCHAR(36),
                               NAME VARCHAR(64) UNIQUE NOT NULL,
                               PRIMARY KEY (COLUUID));''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_OBJ (
                               OBJUUID VARCHAR(36),
                               COLUUID VARCHAR(36),
                               VALUE BLOB NOT NULL,
                               PRIMARY KEY (OBJUUID),
                               FOREIGN KEY (COLUUID) REFERENCES TBL_JSON_COL(COLUUID) ON DELETE CASCADE);''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_ATTR (
                               COLUUID VARCHAR(36),
                               ATTRIBUTE VARCHAR(64),
                               PATH VARCHAR(64),
                               PRIMARY KEY (COLUUID, ATTRIBUTE),
                               FOREIGN KEY (COLUUID) REFERENCES TBL_JSON_COL(COLUUID) ON DELETE CASCADE);''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS TBL_JSON_IDX (
                               OBJUUID VARCHAR(36),
                               COLUUID VARCHAR(36),
                               ATTRIBUTE VARCHAR(64),
                               VALUE VARCHAR(64),
                               PRIMARY KEY (OBJUUID, ATTRIBUTE),
                               FOREIGN KEY (OBJUUID) REFERENCES TBL_JSON_OBJ(OBJUUID) ON DELETE CASCADE,
                               FOREIGN KEY (COLUUID, ATTRIBUTE) REFERENCES TBL_JSON_ATTR(COLUUID, ATTRIBUTE) ON DELETE CASCADE);''')
        
        self.connection.commit()
        
        DOCUMENT_LOCK.release()
        
        Timer(3600, self.vacuum)
    
    def vacuum(self):
        Timer(3600, self.vacuum)
        
        try:
            DOCUMENT_LOCK.acquire()
            self.cursor.execute("VACUUM;")
            self.connection.commit()
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
    
    def create_object(self, coluuid, objuuid):
        try:
            DOCUMENT_LOCK.acquire()
            self.cursor.execute("insert into TBL_JSON_OBJ (COLUUID, OBJUUID, VALUE) values (?, ?, ?);", \
                                (str(coluuid), str(objuuid), self.cipher.encrypt(pickle.dumps({"objuuid" : objuuid, "coluuid" : coluuid}))))
            self.connection.commit()
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
    
    def set_object(self, coluuid, objuuid, object):
        try:
            DOCUMENT_LOCK.acquire()
            object["objuuid"] = objuuid
            object["coluuid"] = coluuid
            self.cursor.execute("update TBL_JSON_OBJ set VALUE = ? where OBJUUID = ?;", \
                                (self.cipher.encrypt(pickle.dumps(object)), str(objuuid)))
            self.connection.commit()

            self.cursor.execute("delete from TBL_JSON_IDX where OBJUUID = ?;", (objuuid,))
            self.connection.commit()
        
            attributes = self.list_attributes(coluuid)
            for attribute_name in attributes:
                try:
                    self.cursor.execute("""insert into TBL_JSON_IDX (OBJUUID, COLUUID, ATTRIBUTE, VALUE) 
                                        values (?, ?, ?, ?);""", \
                                        (str(objuuid), \
                                         str(coluuid), \
                                         str(attribute_name), \
                                         str(eval("str(self.get_object(objuuid)" + attributes[attribute_name] + ")"))))
                    self.connection.commit()
                except Exception:
                    #print traceback.format_exc()
                    pass
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
        
    def get_object(self, objuuid):
        self.cursor.execute("select VALUE from TBL_JSON_OBJ where OBJUUID = ?;", (str(objuuid),))
        self.connection.commit()
        return pickle.loads(self.cipher.decrypt(self.cursor.fetchall()[0][0]))
    
    def find_objects(self, coluuid, attribute, value):
        self.cursor.execute("select OBJUUID from TBL_JSON_IDX where ATTRIBUTE = ? and VALUE = ? and COLUUID = ?;", \
                            (str(attribute), str(value), str(coluuid)))
        self.connection.commit()
        objuuids = []
        for row in self.cursor.fetchall():
            objuuids.append(row[0])
        return objuuids
    
    def delete_object(self, objuuid):
        try:
            DOCUMENT_LOCK.acquire()
            self.cursor.execute("delete from TBL_JSON_OBJ where OBJUUID = ?;", (str(objuuid),))
            self.connection.commit()
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
    
    def create_attribute(self, coluuid, attribute, path):
        try:
            DOCUMENT_LOCK.acquire()
            self.cursor.execute("insert into TBL_JSON_ATTR (COLUUID, ATTRIBUTE, PATH) values (?, ?, ?);", \
                                (str(coluuid), str(attribute), str(path)))
            self.connection.commit()
        
            self.cursor.execute("delete from TBL_JSON_IDX where ATTRIBUTE = ? and COLUUID = ?;", (str(attribute), str(coluuid)))
            self.connection.commit()
        
            self.cursor.execute("select OBJUUID, VALUE from TBL_JSON_OBJ where COLUUID = ?;", (str(coluuid),))
            self.connection.commit()
            objects = {}
            for row in self.cursor.fetchall():
                objects[row[0]] = pickle.loads(self.cipher.decrypt(row[1]))
        
            for objuuid in objects:
                try:
                    self.cursor.execute("""insert into TBL_JSON_IDX (OBJUUID, COLUUID, ATTRIBUTE, VALUE) 
                                        values (?, ?, ?, ?);""", \
                                        (str(objuuid), \
                                         str(coluuid), \
                                         str(attribute), \
                                         str(eval("str(objects[objuuid]" + path + ")"))))
                    self.connection.commit()
                except Exception:
                    traceback.format_exc()
        
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
    
    def delete_attribute(self, coluuid, attribute):
        try:
            DOCUMENT_LOCK.acquire()
            self.cursor.execute("delete from TBL_JSON_ATTR where COLUUID = ? and ATTRIBUTE = ?;", \
                                (str(coluuid), str(attribute)))
            self.connection.commit()
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
        
    def list_attributes(self, coluuid):
        self.cursor.execute("select ATTRIBUTE, PATH from TBL_JSON_ATTR where COLUUID = ?;", (str(coluuid),))
        self.connection.commit()
        
        attributes = {}
        for row in self.cursor.fetchall():
            attributes[row[0]] = row[1]
        return attributes
    
    def create_collection(self, uuid = None, name = "New Collection"):
        try:
            DOCUMENT_LOCK.acquire()
            if not uuid:
                uuid = sucky_uuid()
            
            self.cursor.execute("insert into TBL_JSON_COL (COLUUID, NAME) values (?, ?);", \
                                (str(uuid), str(name)))
            self.connection.commit()
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
        return uuid
    
    def delete_collection(self, uuid):
        try:
            DOCUMENT_LOCK.acquire()
            self.cursor.execute("delete from TBL_JSON_COL where COLUUID = ?;", (str(uuid),))
            self.connection.commit()
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
    
    def rename_collection(self, uuid, name):
        try:
            DOCUMENT_LOCK.acquire()
            self.cursor.execute("update TBL_JSON_COL set NAME = ? where COLUUID = ?;", \
                                (str(name), str(uuid)))
            self.connection.commit()
        except Exception:
            print traceback.format_exc()
        finally:
            self.connection.commit()
            DOCUMENT_LOCK.release()
    
    def list_collections(self):
        self.cursor.execute("select NAME, COLUUID from TBL_JSON_COL;")
        self.connection.commit()
            
        collections = {}
        for row in self.cursor.fetchall():
            collections[row[0]] = row[1]
        return collections
    
    def list_collection_objects(self, coluuid):
        self.cursor.execute("select OBJUUID from TBL_JSON_OBJ where COLUUID = ?;", (coluuid,))
        self.connection.commit()
            
        objuuids = []
        for row in self.cursor.fetchall():
            objuuids.append(row[0])
        return objuuids
    
    def __del__(self):
        self.connection.close()

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
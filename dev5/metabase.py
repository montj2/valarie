#!/usr/bin/python
################################################################################
# VALARIEDB METABASE CONVERSION
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 12/28/2016 Original construction
################################################################################

import sqlite3
import traceback

from .model.inventory import create_status_code, \
                             create_container, \
                             delete_node, \
                             create_task, \
                             create_rfc, \
                             create_procedure, \
                             set_parent_objuuid, \
                             create_host, \
                             create_controller, \
                             create_console, \
                             create_link
                             
from .model.document import Collection

inventory = Collection("inventory")
current_objuuids = inventory.list_objuuids()

conn = sqlite3.connect("metabase.db", 300)
cur = conn.cursor()

rfc_num_to_uuid = {}
tskuuids = []
prcuuids = []

def load():
    metabase_container = create_container("#", "metabase")

    
    status_codes = []
    for status in inventory.find(type = "status"):
        try:
            status_codes.append(int(status.object["code"]))
        except Exception:
            print traceback.format_exc()
    
    cur.execute("select CODE, ALIAS, FRIENDLYTXT, TILETXT, CFGCOLOR, CBGCOLOR, SFGCOLOR, SBGCOLOR from STATUS;")
    conn.commit()
    
    status_container = create_container(metabase_container.objuuid, "Status Codes")
    
    for row in cur.fetchall():
        if int(row[0]) not in status_codes:
            status = create_status_code(status_container.objuuid, row[2])
            
            status.object["alias"] = row[1]
            status.object["code"] = str(row[0])
            status.object["abbreviation"] = row[3]
            status.object["cfg"] = str(row[4]).replace("#", "")
            status.object["cbg"] = str(row[5]).replace("#", "")
            status.object["sfg"] = str(row[6]).replace("#", "")
            status.object["sbg"] = str(row[7]).replace("#", "")
            
            status.set()
            
            print "imported status code: {0}, alias: {1}, name: {2}". \
                  format(status.object["code"], status.object["alias"], status.object["name"])
    
    consoles_container = create_container(metabase_container.objuuid, "Consoles")
    
    ssh_console = create_console(consoles_container.objuuid, "SSH", "99225302-9d6e-8806-0165-d467eb4d3323")
        
    ssh_console.object["body"] = '''#!/usr/bin/python
################################################################################
# SSH CLI
# 
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# SSH command line interface class. This class is a wrapper for os.popen. Each
# console object maitains a continuous ssh session to the specified remote host
# using specified credentials.
#
# 12/10/2014 Original construction
# 12/18/2014 Added mysql method
# 12/31/2014 Added cmp_mysql_password method
#            Added cmp_mysql_username method
#            Modified system method to concatanate stderr and stdout if status
#            is not 0
# 01/05/2015 Added return tuple parameter to system
#            Added sftp member
# 01/07/2015 Applied replace("[sudo] password for " + self.__username + ":", "")
#            to stderr and stdout buffers
# 01/12/2015 Applied replace to stderr buffer
# 01/14/2015 Changed mysql method to run without sudo and supply the mysql
#               password through stdin interactively. This is a fix for the
#               mysql credentials being exposed in /var/log/secure.
# 02/17/2015 Allowed MySQL credentials to be overridded with optional parameters
#               supplied to the MySQL method.
# 04/24/2015 Updated string formatting to shift away from += and + operators for
#               long strings.
# 04/27/2015 Added MySQL dump and MySQL batch methods.
#            Return tuple optional parameter has been added to the Mysql 
#               methods.
# 08/07/2015 Adjusted formatting statements to be compatible with Python 2.6.6
# 08/17/2015 Added get_shell method for asynchronous channel interaction
# 09/01/2015 Removed sudo testing from connect method
# 10/05/2015 Added optional parameter to system to defer from elevating to sudo.
# 10/14/2015 Added session variables and extended logging
# 01/27/2016 Added RSA key based auth
# 04/26/2016 Added lossy ascii character set conversion to mysql and system
#               methods
# 05/23/2016 Added password inspection methods
# 09/07/2016 Added SSH forwarding for MySQL.
# 09/12/2016 Added SSH tunnel methods.
# 01/10/2016 Added Terminal send/recv methods
################################################################################

import paramiko
import pymysql
import select
import ldap
import socket
import SocketServer

from time import time
from threading import Thread
from random import randrange

class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

def verbose(text):
    #print text
    pass
    
class Handler (SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel('direct-tcpip',
                                                   (self.chain_host, self.chain_port),
                                                   self.request.getpeername())
        except Exception as e:
            verbose('Incoming request to %s:%d failed: %s' % (self.chain_host,
                                                              self.chain_port,
                                                              repr(e)))
            return
        if chan is None:
            verbose('Incoming request to %s:%d was rejected by the SSH server.' %
                    (self.chain_host, self.chain_port))
            return

        verbose('Connected!  Tunnel open %r -> %r -> %r' % (self.request.getpeername(),
                                                            chan.getpeername(), (self.chain_host, self.chain_port)))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
                
        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        verbose('Tunnel closed from %r' % (peername,))

class Console:
    def __init__(self, **kargs):
        # Private Members
        self.__ssh = paramiko.SSHClient()
        self.__username = kargs["session"]["ssh username"]
        self.__password = kargs["session"]["ssh password"]
        self.__private_key = None
        self.__remote = kargs["host"]
        self.__mysql_username = kargs["session"]["mysql username"]
        self.__mysql_password = kargs["session"]["mysql password"]
        self.__mysql_remote = None
        self.__session_var = {}
        self.__tunnel = {}
        
        # Public Members
        self.sftp = None
        
        self.connect()
        
        self.__chan = self.__ssh.invoke_shell()

    #### Mutation Methods ########################
    def set_username(self, username):
        self.__username = username
        
    def set_password(self, password):
        self.__password = password
    
    def set_private_key(self, key_filename, password = None):
        self.__private_key = paramiko.RSAKey.from_private_key_file(key_filename, password = password)

    def set_remote_host(self, remote):
        self.__remote = remote
    
    def set_mysql_username(self, username):
        self.__mysql_username = username
        
    def set_mysql_password(self, password):
        self.__mysql_password = password
        
    def set_mysql_remote(self, remote):
        self.__mysql_remote = remote
    
    #### Set Key Value ###########################
    def set(self, key, value):
        try:
            self.__session_var[key] = value
        except Exception:
            self.__session_var = {}
            self.__session_var[key] = value
    
    #### Inspection Methods ######################
    def get_username(self):
        return self.__username
    
    def get_password(self):
        return self.__password
    
    def get_remote_host(self):
        return self.__remote
    
    def get_mysql_username(self):
        return self.__mysql_username
    
    def get_mysql_password(self):
        return self.__mysql_password
        
    def get_mysql_remote(self):
        return self.__mysql_remote
    
    #### Get Key Value ###########################
    # Return key value. If a key error exception is thrown, return none.
    def get(self, key):
        try:
            value = self.__session_var[key]
            return value
        except Exception as e:
            return None
    
    #### Test sudo ###############################
    # Test sudo by sudoing whoami. Credentials are fed into standard input and
    # flushed after executing sudo. If a non-zero return code is recieved a
    # custom exception is raised.
    def __test_sudo(self):
        if not self.__username == "root":
            stdin, stdout, stderr = self.__ssh.exec_command('sudo -S whoami')
            stdin.write(self.__password + '\n')
            stdin.flush()
            if 0 != int(stdout.channel.recv_exit_status()):
                raise NameError('Sudo test failed with {0}@{1}'.format(self.__username, self.__remote))
    
    #### Connect to SSH Server ###################
    # Set host key policy to AutoAddPolicy() and connect to host using credentials
    # from private members. Finally test sudo.
    def connect(self):
        self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.__private_key:        
            self.__ssh.connect(self.__remote, username = self.__username, pkey = self.__private_key)
        else:
            self.__ssh.connect(self.__remote, username = self.__username, password = self.__password)
        self.__ssh.get_transport().set_keepalive(30)
        self.sftp = self.__ssh.open_sftp()
    
    #### Close Connection ########################
    # Close SFTP and SSH connections
    def close(self):
        self.sftp.close()
        self.__ssh.close()
    
    #### Get Shell ###############################
    # Return channel object for an interactive shell
    def get_shell(self):
        return self.__ssh.invoke_shell()

    #### System Command ##########################
    # Execute command on SSHClient. If the credentials has a user other than root
    # append the command into a sudo command. If redirection is used with sudo,
    # run the command in its own bash shell to preserve privileges while
    # redirecting to a file. If __debug is set to true, print all three I/O
    # streams during execution. If a non-zero exit code is returned, tag the
    # standard error buffer as red font and add it to the output buffer. If the
    # return tuple parameter is set to true, a tuple of the exit status, standard
    # output buffer, and standard error buffer is returned.
    def system(self, command, return_tuple = False, sudo_command = True):
        if self.__username == "root" or not sudo_command:
            stdin, stdout, stderr = self.__ssh.exec_command(command)
        else:
            if " > " in command or " >> " in command:
                stdin, stdout, stderr = self.__ssh.exec_command("sudo -S bash -c '{0}'".format(command))
            else:
                stdin, stdout, stderr = self.__ssh.exec_command('sudo -S ' + command)
            stdin.write(self.__password + '\n')
            stdin.flush()

        # Lossy ascii character set conversion
        output_buffer = ""
        for c in stdout.read().replace("[sudo] password for {0}:".format(self.__username), ""):
            try:
                output_buffer += c.encode("ascii", "ignore")
            except Exception:
                pass

        # Lossy ascii character set conversion
        stderr_buffer = ""
        for c in stderr.read().replace("[sudo] password for {0}:".format(self.__username), ""):
            try:
                stderr_buffer += c.encode("ascii", "ignore")
            except Exception:
                pass
        
        status = stdout.channel.recv_exit_status()
        
        if return_tuple:
            return status, output_buffer, stderr_buffer
        elif 0 != int(status):
            return '{0}<font color="red"><br>{1}</font><br>'.format(output_buffer, stderr_buffer)
        else:
            return output_buffer
    
    #### SSH Tunnel ##############################
    # Methods for starting and stopping SSH tunnels. 
    def __start_tunnel(self, local_port, remote_host, remote_port):
        transport = self.__ssh.get_transport()
        class SubHandler (Handler):
            chain_host = remote_host
            chain_port = remote_port
            ssh_transport = transport
        self.__tunnel[local_port] = ForwardServer(('', local_port), SubHandler)
        self.__tunnel[local_port].serve_forever()
    
    def start_tunnel(self, local_port, remote_host, remote_port):    
        Thread(target = self.__start_tunnel, args = (local_port, remote_host, remote_port)).start()
    
    def stop_tunnel(self, local_port):
        self.__tunnel[local_port].shutdown()
        del self.__tunnel[local_port]
    
    #### MySQL Query #############################
    # Assemble a MySQL batch query using the MySQL remote host and credentials
    # members. If the remote host is set to none, assume localhost when
    # running the query. MySQL credentials can be overridded as optional 
    # parameters supplied to the mysql method. Original method has been 
    # overhauled to forward pymysql connections over SSH rather than using
    # remote clients.
    def mysql(self, \
              query, \
              password = None, \
              username = None, \
              mysql_remote = None, \
              return_tuple = False):
        if not password:
            password = self.__mysql_password

        if not username:
            username = self.__mysql_username

        if not mysql_remote:
            mysql_remote = self.__mysql_remote

        if not username or not password:
            raise Exception('MySQL query attempted without credentials set.')
        
        try:
            local_port = randrange(0, 1000, 1) + 50000
            self.start_tunnel(local_port, mysql_remote, 3306)
            
            conn = pymysql.connect(host = "127.0.0.1", port = local_port, user = username, passwd = password)
            cur = conn.cursor()

            try:
                cur.execute(query)
                conn.commit()
                
                output_buffer = ""
                for row in cur.fetchall():
                    output_buffer += "\n"
                    for i, col in enumerate(row):
                        output_buffer += str(col)
                        if i < len(row) - 1:
                            output_buffer += "\t"
                    
                stderr_buffer = ""
                status = 0
            except Exception as e:
                output_buffer = ""
                stderr_buffer = str(e)
                status = 1
            
            conn.close()
        except Exception as e:
            output_buffer = ""
            stderr_buffer = str(e)
            status = 1
        finally:
            self.stop_tunnel(local_port)
        
        if return_tuple:
            return status, output_buffer, stderr_buffer
        elif 0 != int(status):
            return '{0}<font color="red"><br>{1}</font><br>'.format(output_buffer, stderr_buffer)
        else:
            return output_buffer
        
    def cmp_mysql_password(self, password):
        return password == self.__mysql_password

    def cmp_mysql_username(self, username):
        return username == self.__mysql_username

    #### LDAP Query ##############################
    def ldap(self, ldap_remote, dn, pw, base_dn, return_tuple = False):
        try:
            output_buffer = ""
            
            local_port = randrange(0, 1000, 1) + 50000
            self.start_tunnel(local_port, ldap_remote, 636)
            output_buffer += "Tunnel localhost:{0} > {1}:636\n".format(local_port, ldap_remote)
            
            conn = ldap.initialize('ldaps://127.0.0.1:{0}'.format(local_port))
            output_buffer += "Initialized ldaps://127.0.0.1:{0}\n".format(local_port)
            
            conn.protocol_version = ldap.VERSION3
            conn.set_option(ldap.OPT_REFERRALS, 0)
            
            #conn.start_tls_s
            
            conn.simple_bind(dn, pw)
            output_buffer += "Binding...\n"
            output_buffer += dn + "\n"
            
            try:
                filter = '(objectclass=person)'
                attrs = ['sn']
                
                output_buffer += "Query...\n"
                
                for row in conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs):
                    output_buffer += "{0}\n".format(str(row))
                
                
                stderr_buffer = ""
                status = 0
            except Exception as e:
                stderr_buffer = str(e)
                status = 1
            
            conn.unbind()
        except Exception as e:
            stderr_buffer = str(e)
            status = 1
        finally:
            #pass
            self.stop_tunnel(local_port)
        
        if return_tuple:
            return status, output_buffer, stderr_buffer
        elif 0 != int(status):
            return '{0}<font color="red"><br>{1}</font><br>'.format(output_buffer, stderr_buffer)
        else:
            return output_buffer
    
    #### Tunnel Scan #############################
    def tscan(self, remote_host, remote_port, return_tuple = False):
        try:
            output_buffer = ""
            stderr_buffer = ""
            status = 1
            
            local_port = randrange(0, 1000, 1) + 50000
            self.start_tunnel(local_port, remote_host, remote_port)
            output_buffer += "Tunnel localhost:{0} > {1}:{2}\n".format(local_port, remote_host, remote_port)
            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect(('localhost', local_port))
                s.send(b'\n\n')
                s.recv(1)
                status = 0
            except Exception as e:
                stderr_buffer = str(e)
            finally:
                s.close()
            
            if status == 0:
                output_buffer += "{0}:{1} open.\n".format(remote_host, remote_port)
            else:
                output_buffer += "{0}:{1} closed.\n".format(remote_host, remote_port)

        except Exception as e:
            stderr_buffer = str(e)
        finally:
            #pass
            self.stop_tunnel(local_port)
        
        if return_tuple:
            return status, output_buffer, stderr_buffer
        elif 0 != int(status):
            return '{0}<font color="red"><br>{1}</font><br>'.format(output_buffer, stderr_buffer)
        else:
            return output_buffer
    
    def send(self, input_buffer):
        for c in input_buffer:
            self.__chan.send(c)
    
    def recv(self):
        if self.__chan.recv_ready():
            return self.__chan.recv(9999)
        elif self.__chan.recv_stderr_ready():
            return self.__chan.recv_stderr(9999)
        else:
            return '' '''
    
    ssh_console.set()
    
    print "imported SSH console..."
    
    
    
    
    cur.execute("select HSTUUID, HOST, NAME from HOST;")
    conn.commit()
    
    hosts_container = create_container(metabase_container.objuuid, "Hosts")
    
    for row in cur.fetchall():
        if row[0] in current_objuuids:
            #delete_node(row[0])
            pass
        else:
            host = create_host(hosts_container.objuuid, row[2], row[0])
        
            host.object["host"] = row[1]
            host.object["console"] = ssh_console.objuuid
        
            host.set()
        
            print "imported host: {0}, name: {1}".format(host.object["host"], host.object["name"])
    
    rfcs_container = create_container(metabase_container.objuuid, "RFCs")
    
    cur.execute("select RFCNUM, TITLE, DESCRIPTION, NAME, EMAIL, PHONE from RFC;")
    conn.commit()

    for row in cur.fetchall():
        rfc = create_rfc(rfcs_container.objuuid)
        
        rfc.object["description"] = row[2]
        rfc.object["title"] = row[1]
        rfc.object["poc name"] = row[3]
        rfc.object["poc phone"] = row[5]
        rfc.object["poc email"] = row[4]
        rfc.object["number"] = str(row[0])
            
        if row[1] == "":
            rfc.object["name"] = "RFC {0}".format(str(row[0]))
        else:
            rfc.object["name"] = "RFC {0} - {1}".format(str(row[0]), row[1])
            
        rfc.set()
        
        rfc_num_to_uuid[int(row[0])] = rfc.objuuid
        
        print "imported rfc number: {0}, name: {1}".format(rfc.object["number"], rfc.object["name"])

    
    
    cur.execute("select CTRUUID, NAME from CONTROLLER;")
    conn.commit()
    
    controllers_container = create_container(metabase_container.objuuid, "Controllers")
    tasks_container = create_container(metabase_container.objuuid, "Tasks")
    procedures_container = create_container(metabase_container.objuuid, "Procedures")
    
    for row in cur.fetchall():
        if row[0] in current_objuuids:
            #delete_node(row[0])
            pass
        else:
            controller_container = create_container(controllers_container.objuuid, row[1])
            host_links_container = create_container(controller_container.objuuid, "Host Links")
            procedure_links_container = create_container(controller_container.objuuid, "Procedure Links")
            
            controller = create_controller(controller_container.objuuid, row[1], row[0])
            
            
            cur.execute("select distinct HSTUUID from CONTHST where CTRUUID = ?;", (row[0],))
            conn.commit()
            for host_row in cur.fetchall():
                controller.object["hosts"].append(host_row[0])
                create_link(host_row[0], host_links_container.objuuid)
            
            cur.execute("select distinct PRCUUID from CONTSEQ where CTRUUID = ?;", (row[0],))
            conn.commit()
            for procedure_row in cur.fetchall():
                try:
                    controller.object["procedures"].append(load_procedure(procedure_row[0], procedures_container.objuuid, tasks_container).objuuid)
                    create_link(procedure_row[0], procedure_links_container.objuuid)
                except Exception:
                    print traceback.format_exc()
                
                cur.execute("select distinct LNKUUID from PROCLNK where PRCUUID = ?;", (procedure_row[0],))
                conn.commit()
                for rel_procedure_row in cur.fetchall():
                    try:
                        load_procedure(rel_procedure_row[0], procedures_container.objuuid, tasks_container)
                        create_link(rel_procedure_row[0], procedure_links_container.objuuid)
                    except Exception:
                        print traceback.format_exc()
            
            controller.set()
        
            print "imported controller: {0}".format(row[1])

def load_procedure(prcuuid, parent_objuuid, tasks_container):
    cur.execute("select NAME, TSKCONTINUE, TITLE, DISCUSSION from TBL_PROCEDURE where PRCUUID = ?;", (prcuuid,))
    conn.commit()
    row = cur.fetchall()[0]

    if prcuuid not in prcuuids:
        prcuuids.append(prcuuid)
        procedure = create_procedure(parent_objuuid, row[0], prcuuid)
        
        procedure.object["title"] = row[2]
        procedure.object["description"] = row[3]
            
        for continue_code_str in row[1].split(","):
            try:
                procedure.object["continue {0}".format(continue_code_str)] = "true"
            except Exception:
                print traceback.format_exc()
            
        cur.execute("select TSKUUID from PROCSEQ where PRCUUID = ? order by SEQNUM;", (prcuuid,))
        conn.commit()
        for task_row in cur.fetchall():
            procedure.object["tasks"].append(task_row[0])
            if task_row[0] not in tskuuids:
                tskuuids.append(task_row[0])
                load_task(task_row[0], tasks_container.objuuid)
    
        cur.execute("select distinct RFCNUM from RFC2PRCUUID where PRCUUID = ?;", (prcuuid,))
        conn.commit()
        for rfc_row in cur.fetchall():
            try:
                if rfc_num_to_uuid[int(rfc_row[0])] not in procedure.object["rfcs"]:
                    procedure.object["rfcs"].append(rfc_num_to_uuid[int(rfc_row[0])])
            except Exception:
                print traceback.format_exc()
        
        procedure.set()
        print "imported procedure name: {0}".format(procedure.object["name"])
    
        return procedure
    else:
        return inventory.get_object(prcuuid)

def load_task(tskuuid, parent_objuuid):
    cur.execute("select BODY, NAME from TASK where TSKUUID = ?;", (tskuuid,))
    conn.commit()
    row = cur.fetchall()[0]
    
    task = create_task(parent_objuuid, row[1], tskuuid)
        
    task.object["body"] = str(row[0]).replace("from globals import *", "")
        
    task.set()
        
    print "imported task name: {0}".format(task.object["name"])
    
    return task
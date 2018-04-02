#!/usr/bin/python
################################################################################
# MAIN
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 10/16/2016 Original construction
# 10/19/2016 Created start function
# 01/27/2017 Brought in custom SSL adapter
################################################################################

import cherrypy
import os
import ssl

from cherrypy.wsgiserver.ssl_builtin import BuiltinSSLAdapter
from cherrypy import wsgiserver
from cherrypy.wsgiserver import ssl_adapters  

from .controller.root import Root

class BuiltinSsl(BuiltinSSLAdapter):
    def wrap(self, sock):
        try:
            s = ssl.wrap_socket(
                sock, 
                ciphers = ('ECDH+AES256'),
                do_handshake_on_connect = True,
                server_side = True, 
                certfile = self.certificate,
                keyfile = self.private_key,
                ssl_version = ssl.PROTOCOL_TLSv1_2
            )
        except ssl.SSLError:
            e = sys.exc_info()[1]
            if e.errno == ssl.SSL_ERROR_EOF:
                return None, {}
            elif e.errno == ssl.SSL_ERROR_SSL:
                if e.args[1].endswith('http request'):
                    raise wsgiserver.NoSSLError
                elif e.args[1].endswith('unknown protocol'):
                    return None, {}
            raise

        return s, self.get_environ(s)

ssl_adapters['custom-ssl'] = BuiltinSsl

def start():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    config = {
        'log.screen': False,
        'tools.staticdir.on' : True,
        'tools.sessions.on' : True,
        'tools.sessions.locking' : 'explicit',
        'tools.auth.on' : True,
        'tools.staticdir.dir' : os.path.join(current_dir, './static'),
        'server.thread_pool' : 100,
        'server.socket_host' : '0.0.0.0',
        'server.socket_port' : 443,
        'server.ssl_module' : 'custom-ssl',
        'server.ssl_certificate' : os.path.join(current_dir, './utinhuou.crt'),
        'server.ssl_private_key' : os.path.join(current_dir, './utinhuou.key')
        #'log.error_file': 'error.log'
    }
    
    cherrypy.config.update(config)
    
    cherrypy.quickstart(Root())

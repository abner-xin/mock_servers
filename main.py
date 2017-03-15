from SimpleXMLRPCServer import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn

from my_servers.my_dns_server import MyDNSServer
from my_servers.my_http_server import MyHTTPServer

from logger import logger
from my_servers.my_mail_server import MyMailServer
from my_servers.my_ssh_tunnel_server import MySSHTunnelServer


class RemoteServer(ThreadingMixIn,
                   SimpleXMLRPCServer,
                   MySSHTunnelServer,
                   MyHTTPServer,
                   MyDNSServer,
                   MyMailServer):
    def __init__(self, host='0.0.0.0', port=8270, allow_stop=True):
        SimpleXMLRPCServer.__init__(self, (host, int(port)), logRequests=False, allow_none=True)

        self._server_stop_functions = []
        for cls in RemoteServer.__bases__:
            if cls not in (ThreadingMixIn, SimpleXMLRPCServer):
                cls.__init__(self)
                self._register_my_server_functions(cls)

        self._allow_stop = allow_stop
        logger.info('Remote server [%s:%s] is serving...' % (host, port))
        self.serve_forever()

    def _register_my_server_functions(self, cls):
        for fn in dir(cls):
            if not fn.startswith('_'):
                f = getattr(self, fn)
                if callable(f):
                    self.register_function(f, fn)
                    logger.info("registered function: %s" % fn)

    def stop_remote_server_function(self):
        if self._allow_stop:
            self.shutdown()
        logger.info('Remote server exits...')
        return True


if __name__ == '__main__':
    try:
        RemoteServer()
    except KeyboardInterrupt:
        pass
import threading
import SocketServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from logger import logger


class MyHTTPRequestHandler(SimpleHTTPRequestHandler):

    ROUTES = {}

    @classmethod
    def add_route(cls, bind_port, path):
        cls.ROUTES[bind_port] = path

    @classmethod
    def delete_route(cls, bind_port):
        try:
            del cls.ROUTES[bind_port]
        except KeyError:
            pass

    @classmethod
    def get_path(cls, bind_port):
        try:
            return cls.ROUTES[bind_port]
        except KeyError:
            return None

    def translate_path(self, path):
        bind_port = self.server.server_address[1]
        working_path = MyHTTPRequestHandler.get_path(str(bind_port))
        path = "/%s/%s" % (working_path, path) if working_path else path
        return SimpleHTTPRequestHandler.translate_path(self, path)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class MyHTTPServer:

    def __init__(self):
        self.my_http_servers = {}

    def start_http_server(self, port=80, workspace=None):
        port = str(port)
        http = self.my_http_servers.get(port, None)
        if http:
            self.stop_http_server(port)

        logger.info('HTTP server (%s): starting' % port)

        MyHTTPRequestHandler.add_route(port, workspace)

        http_server = ThreadedTCPServer(('', int(port)), MyHTTPRequestHandler)
        http_thread = threading.Thread(target=http_server.serve_forever)
        http_thread.daemon = True
        http_thread.start()

        self.my_http_servers[port] = {'server_handler': http_server, 'thread_handler': http_thread}

        logger.info('HTTP server (%s): started' % port)

    def stop_http_server(self, port=None):

        def stop(bind_port):
            http_server = self.my_http_servers[bind_port]
            try:
                http_server['server_handler'].shutdown()
                http_server['server_handler'].server_close()
                http_server['thread_handler'].join()
                del self.my_http_servers[bind_port]
            except Exception, error:
                logger.info("Exception when stop HTTP server: %s" % error)
            else:
                logger.info('HTTP server (%s): stopped' % bind_port)
            MyHTTPRequestHandler.delete_route(bind_port)

        if port:
            port = str(port)
            http = self.my_http_servers.get(port, None)
            if http:
                stop(port)
        else:
            for port in self.my_http_servers.keys():
                stop(port)

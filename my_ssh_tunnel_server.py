import threading
from logger import logger
from sshtunnel import SSHTunnelForwarder


class MySSHTunnelServer:
    lock = threading.Lock()
    def __init__(self):
        self.my_ssh_tunnel_servers = {}

    def start_ssh_tunnel_server(self,
                                ssh_address,
                                ssh_username,
                                ssh_password,
                                local_bind_address,
                                remote_bind_address):

        local_bind_port = local_bind_address[1]
        if self.my_ssh_tunnel_servers.get(str(local_bind_port), None):
            self.stop_ssh_tunnel_server(local_bind_port)

        logger.info("SSHTunnel Server (%s): starting" % local_bind_port)
        ssh_tunnel_server = SSHTunnelForwarder(
                                ssh_address=tuple(ssh_address),                     #('1.2.3.4', 22)
                                ssh_username=ssh_username,                          # root
                                ssh_password=ssh_password,                          # 111111
                                local_bind_address=tuple(local_bind_address),       # ('2.3.4.5', 8721)
                                remote_bind_address=tuple(remote_bind_address),     # ('127.0.0.1', 5432)
                                logger=logger
                                )
        ssh_tunnel_server.start()
        with MySSHTunnelServer.lock:
            self.my_ssh_tunnel_servers[str(local_bind_port)] = ssh_tunnel_server
        logger.info("SSHTunnel Server (%s): started" % local_bind_port)

    def stop_ssh_tunnel_server(self, local_bind_port=None):
        def stop(port, handler):
            try:
                handler.close()
            except Exception, error:
                logger.info("Exception when stop sshTunnel (%s): %s" % (port, error))
            with MySSHTunnelServer.lock:
                del self.my_ssh_tunnel_servers[port]
            logger.info("SSHTunnel Server (%s): stopped" % port)

        if local_bind_port:
            logger.info("local_bind_port: %s" % local_bind_port)
            handler = self.my_ssh_tunnel_servers.get(str(local_bind_port), None)
            if handler is not None:
                stop(str(local_bind_port), handler)
        else:
            for port, handler in self.my_ssh_tunnel_servers.items():
                stop(port, handler)
from dnslib.server import DNSServer
from dnslib.zoneresolver import ZoneResolver
from logger import logger


class MyDNSServer:
    def __init__(self):
        self.my_dns_server = None

    def start_dns_server(self, data):
        if self.my_dns_server:
            self.stop_dns_server()
        logger.info("DNS server: starting...")
        self.my_dns_server = DNSServer(ZoneResolver(data), port=53, address="0.0.0.0", tcp=False)
        self.my_dns_server.start_thread()
        logger.info("DNS server: started")

    def stop_dns_server(self):
        if self.my_dns_server:
            self.my_dns_server.stop()
            self.my_dns_server = None
            logger.info("DNS server: stopped")

    def flush_dns_server(self, data):
        if self.my_dns_server is None:
            self.start_dns_server(data)
            return

        self.my_dns_server.server.resolver = ZoneResolver(data)
        logger.info("DNS server: flushed")
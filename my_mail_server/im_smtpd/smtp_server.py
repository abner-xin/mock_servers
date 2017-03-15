import smtpd
import ssl
from .smtp_channel import SMTPChannel
import mock_logger


# import sys
# smtpd.DEBUGSTREAM = sys.stderr

class SMTPServer(smtpd.SMTPServer):
    def __init__(self, localaddr, remoteaddr, ssl_must=False, certfile=None, keyfile=None, cafile=None,
                 require_authentication=False, credential_validator=None, logger=None):
        smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)
        self.ssl_must = ssl_must
        # self.ssl_version = ssl_version
        self.certfile = certfile
        self.keyfile = keyfile if keyfile else self.certfile
        self.cafile = cafile
        self.require_authentication = require_authentication
        self.credential_validator = credential_validator
        self.logger = logger or mock_logger.logger
        self.ssl_ctx = None
        if self.certfile or self.keyfile:
            self.ssl_ctx = self._get_ssl_ctx()

        if self.ssl_must:
            self.logger.info("SSL Must: %s" % self.ssl_must)
        if self.certfile:
            self.logger.info("cert file: %s" % certfile)
        if self.keyfile:
            self.logger.info("key file: %s" % keyfile)

        if self.ssl_must or self.certfile:
            self.is_tls_enabled = True
        else:
            self.is_tls_enabled = False
        # print >> smtpd.DEBUGSTREAM, '\tTLS Mode: %s\n\tTLS Context: %s' % (
        # 'explicit (plaintext until STARTTLS)' if starttls else 'implicit (encrypted from the beginning)')

    def _get_ssl_ctx(self):
        sslctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if self.cafile:
            sslctx.verify_mode = ssl.CERT_REQUIRED
            self.logger.info("need to verify client cert")
            sslctx.load_verify_locations(cafile="san_ca.pem")
        sslctx.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

        return sslctx

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            print >> smtpd.DEBUGSTREAM, 'Incoming connection from %s' % repr(addr)
            if self.is_tls_enabled:
                self.logger.info("TLS is available on Mail Server")
            else:
                self.logger.info("TLS is disabled on Mail Server")
            if self.ssl_must:
                self.logger.info("Must use TLS")
            """
            if self.ssl:
                self.logger.info("explicit, plaintext until STARTTLS")
            elif not self.ssl and (self.certfile or self.keyfile):
                self.logger.info("implicit, encrypted from the beginning.")
                self.logger.warn("it cannot work well now")
                # conn = self.ssl_ctx.wrap_socket(conn, server_side=True)
                # print >> smtpd.DEBUGSTREAM, 'Peer: %s - negotiated TLS: %s' % (repr(addr), repr(conn.cipher()))
            else:
                self.logger.info("plaintext for SMTP session")
            """
            map = None
            channel = SMTPChannel(
                self,
                conn,
                addr,
                require_authentication=self.require_authentication,
                credential_validator=self.credential_validator,
                map=map,
                logger=self.logger
            )
            # channel.debug = True
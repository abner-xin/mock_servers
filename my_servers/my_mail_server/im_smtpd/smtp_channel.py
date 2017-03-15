import asynchat
import base64
import smtpd
import ssl

import mock_logger


def decode_b64(data):
    '''Wrapper for b64decode, without having to struggle with bytestrings.'''
    byte_string = data.encode('utf-8')
    decoded = base64.b64decode(byte_string)
    return decoded.decode('utf-8')


def encode_b64(data):
    '''Wrapper for b64encode, without having to struggle with bytestrings.'''
    byte_string = data.encode('utf-8')
    encoded = base64.b64encode(byte_string)
    return encoded.decode('utf-8')


class SMTPChannel(smtpd.SMTPChannel):
    def __init__(self, smtp_server, newsocket, fromaddr, require_authentication=False, credential_validator=None,
                 map=None, logger=None):
        smtpd.SMTPChannel.__init__(self, smtp_server, newsocket, fromaddr)
        asynchat.async_chat.ac_in_buffer_size = 10 * 1024 * 1024  # assume the max message size is 10M
        asynchat.async_chat.ac_out_buffer_size = 10 * 1024 * 1024  # assume the max message size is 10M
        asynchat.async_chat.__init__(self, newsocket, map=map)


        self.require_authentication = require_authentication
        self.authenticating = False
        self.authenticated = False
        self.username = None
        self.password = None
        self.credential_validator = credential_validator

        self.logger = logger or mock_logger.logger

    def smtp_EHLO(self, arg):
        if not arg:
            self.push('501 Syntax: HELO hostname')
        elif self.__greeting:
            self.push('503 Duplicate HELO/EHLO')
        else:
            self.__greeting = arg
            push_list = [('250', self.__fqdn),]
            if self.__server.require_authentication or self.__server.credential_validator:
                push_list.append(('250', 'AUTH LOGIN PLAIN'))
            if self.__server.is_tls_enabled and not isinstance(self.__conn, ssl.SSLSocket):
                push_list.append(('250', 'STARTTLS'))

            if len(push_list) > 1:
                for msg in push_list[:-1]:
                    self.push('-'.join(msg))
            self.push(' '.join(push_list[-1])) # The last line should be joined by ' '

    def smtp_STARTTLS(self, arg):
        self.logger.info("starttls starting...")
        if arg:
            self.push('501 Syntax error (no parameters allowed)')
            self.logger.info("starttls failed: Syntax error (no parameters allowed)")
        elif self.__server.is_tls_enabled and not isinstance(self.__conn, ssl.SSLSocket):
            self.push('220 Ready to start TLS')
            self.__conn.settimeout(30)
            try:
                self.__conn = self.__server.ssl_ctx.wrap_socket(self.__conn, server_side=True)
            except ssl.SSLError, err:
                self.logger.info("handshake error: %s" % err)
                self.push('531 %s' % err)
                return
            else:
                self.logger.info("SSL handshake success")
            self.__conn.settimeout(None)
            # re-init channel
            asynchat.async_chat.__init__(self, self.__conn)
            self.__line = []
            self.__state = self.COMMAND
            self.__greeting = 0
            self.__mailfrom = None
            self.__rcpttos = []
            self.__data = ''
            self.logger.info('Peer 1: %s - negotiated TLS: %s' % (repr(self.__addr), repr(self.__conn.cipher())))
            # print >> smtpd.DEBUGSTREAM, 'Peer 1: %s - negotiated TLS: %s' % (
            #     repr(self.__addr), repr(self.__conn.cipher()))
            self.logger.info("starttls: OK")
        else:
            self.push('454 TLS not available due to temporary reason')
            self.logger.info("starttls failed: TLS not available due to temporary reason")

    def smtp_MAIL(self, arg):
        address = self.__getaddr('FROM:', arg) if arg else None
        if not address:
            self.push('501 Syntax: MAIL FROM:<address>')
            return
        if self.__mailfrom:
            self.push('503 Error: nested MAIL command')
            return
        if self.__server.ssl_must and not isinstance(self.__conn, ssl.SSLSocket):
            self.push('530 Error: MUST use TLS')
            return
        self.__mailfrom = address
        self.push('250 Ok')

    def smtp_AUTH(self, arg):
        if 'PLAIN' in arg:
            split_args = arg.split(' ')
            # second arg is Base64-encoded string of blah\0username\0password
            authbits = decode_b64(split_args[1]).split('\0')
            self.username = authbits[1]
            self.password = authbits[2]
            if self.credential_validator and self.credential_validator.validate(self.username, self.password):
                self.authenticated = True
                self.push('235 Authentication successful.')
            else:
                self.push('454 Temporary authentication failure.')
                # raise ExitNow()
                self.close_when_done()
        elif 'LOGIN' in arg:
            self.authenticating = True
            split_args = arg.split(' ')

            # Some implmentations of 'LOGIN' seem to provide the username
            # along with the 'LOGIN' stanza, hence both situations are
            # handled.
            if len(split_args) == 2:
                self.username = decode_b64(arg.split(' ')[1])
                self.push('334 ' + encode_b64('Username'))
            else:
                self.push('334 ' + encode_b64('Username'))

        elif not self.username:
            self.username = decode_b64(arg)
            self.push('334 ' + encode_b64('Password'))
        else:
            self.authenticating = False
            self.password = decode_b64(arg)
            if self.credential_validator and self.credential_validator.validate(self.username, self.password):
                self.authenticated = True
                self.push('235 Authentication successful.')
            else:
                self.push('454 Temporary authentication failure.')
                # raise ExitNow()
                self.close_when_done()
    # This code is taken directly from the underlying smtpd.SMTPChannel
    # support for AUTH is added.
    def found_terminator(self):
        line = smtpd.EMPTYSTRING.join(self.__line)

        if self.debug:
            self.logger.info('found_terminator(): data: %s' % str(line))

        self.__line = []
        if self.__state == self.COMMAND:
            if not line:
                self.push('500 Error: bad syntax')
                return
            method = None
            i = line.find(' ')

            if self.authenticating:
                # If we are in an authenticating state, call the
                # method smtp_AUTH.
                arg = line.strip()
                command = 'AUTH'
            elif i < 0:
                command = line.upper()
                arg = None
            else:
                command = line[:i].upper()
                arg = line[i + 1:].strip()

            # White list of operations that are allowed prior to AUTH.
            if not command in ['AUTH', 'EHLO', 'HELO', 'NOOP', 'RSET', 'QUIT', 'STARTTLS']:
                if self.require_authentication and not self.authenticated:
                    self.push('530 Authentication required')
                    return

            method = getattr(self, 'smtp_' + command, None)
            if not method:
                self.push('502 Error: command "%s" not implemented' % command)
                return
            method(arg)
            return
        else:
            if self.__state != self.DATA:
                self.push('451 Internal confusion')
                return
            # Remove extraneous carriage returns and de-transparency according
            # to RFC 821, Section 4.5.2.
            data = []
            for text in line.split('\r\n'):
                if text and text[0] == '.':
                    data.append(text[1:])
                else:
                    data.append(text)
            self.__data = smtpd.NEWLINE.join(data)
            status = self.__server.process_message(
                self.__peer,
                self.__mailfrom,
                self.__rcpttos,
                self.__data
            )
            self.__rcpttos = []
            self.__mailfrom = None
            self.__state = self.COMMAND
            self.set_terminator('\r\n')
            if not status:
                self.push('250 Ok')
            else:
                self.push(status)
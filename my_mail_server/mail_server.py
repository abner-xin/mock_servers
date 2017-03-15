from .im_smtpd.mock_logger import logger


def start_mail_server(args):
    import asyncore
    from .im_smtpd import SMTPServer
    from .im_smtpd.mailbox import MailBoxManagement
    from .im_smtpd.validator import CredentialValidator
    from logger import logger

    class CusSMTPServer(SMTPServer):
        def process_message(self, peer, mailfrom, rcpttos, message_data):
            self.logger.info("message come from: %s" % str(peer))
            self.logger.info("message from: %s" % mailfrom)
            self.logger.info("message rcpt: %s" % str(rcpttos))
            self.logger.info("message length: %s" % len(message_data))
            local_bind_port = self._localaddr[1]
            self.logger.info("local bind port: %s" % local_bind_port)
            for rcpt in rcpttos:
                MailBoxManagement(local_bind_port, self.logger).deliver_mail(rcpt.strip(), message_data)

    args = [o for o in args]
    args_defines = ('localaddr', 'remoteaddr', 'ssl_must', 'certfile', 'keyfile', 'cafile',
                    'require_authentication', 'credential_validator', 'logger')
    args_dict = dict(zip(args_defines[:len(args)], args))

    logger.info("start mail server with args dict: %s" % args_dict)

    if args_dict.get('require_authentication', None):
        validator = CredentialValidator(logger=logger)
        for user, password in args_dict['credential_validator'].items():
            validator.add_one_account(user, password)
        args[args_defines.index('credential_validator')] = validator
    args[args_defines.index('localaddr')] = tuple(args_dict['localaddr'])
    # logger.info("start mail server with args: %s" % args)
    mail_server = CusSMTPServer(*args, logger=logger)
    asyncore.loop()




import multiprocessing

import shutil

from .im_smtpd import MailBoxManagement
from logger import logger
import mail_server

# a fake account
pop3_account = 'pop3@pop3.com'


class MyMailServer:

    def __init__(self):
        self.my_mail_servers = {}

    def _start_default_mail_server(self):
        self.start_mail_server(('0.0.0.0',25), None)

    def start_mail_server(self, *args):
        local_addr = args[0]
        port = str(local_addr[1])

        if self.my_mail_servers.get(port, None):
            self.stop_mail_server(port)

        logger.info('Mail server (%s): starting' % port)

        mail_server_process = multiprocessing.Process(target=mail_server.start_mail_server, args=(args,))
        mail_server_process.start()

        self.my_mail_servers[port] = mail_server_process
        logger.info('Mail server (%s): started' % port)

    def stop_mail_server(self, port=None):
        def stop(port):
            try:
                self.my_mail_servers[port].terminate()
                self.my_mail_servers[port].join()
                # logger.info("mail process is exited")
            except Exception, error:
                logger.info("Exception when stop Mail server: %s" % error)
            else:
                logger.info('Mail server (%s): stopped' % port)
            del self.my_mail_servers[port]

        if port:
            port = str(port)
            if self.my_mail_servers.get(port, None):
                stop(port)
        else:
            for port in self.my_mail_servers.keys():
                stop(port)
            self._start_default_mail_server() # default mail server will not be stopped.

    def clear_all_mailboxes(self):
        for mailbox in MailBoxManagement.get_all_mailboxes():
            shutil.rmtree(mailbox)
            logger.info("cleared mailbox: %s" % mailbox)
        logger.info("cleared all mailboxes.")

    def clear_mailbox(self, port, user=None):
        m = MailBoxManagement(port, logger=logger)
        m.clear_mailbox(user)

    def get_mail_from_mailbox(self, port, user):
        m = MailBoxManagement(port, logger=logger)
        return m.get_mail(recipient=user)

    def start_pop3_server(self, port):

        if self.my_mail_servers.get(str(port), None):
            self.stop_pop3_server(port)

        from .pop3.pypopper import serve

        logger.info("POP3 Server (%s): starting" % port)
        m = MailBoxManagement(port, logger=logger)
        email_files = m.get_mail_from_mailbox(pop3_account)
        pop3_server_process = multiprocessing.Process(target=serve, args=('0.0.0.0', int(port), email_files[0]))
        pop3_server_process.start()

        self.my_mail_servers[str(port)] = pop3_server_process

        logger.info("POP3 Server (%s): started" % port)

    def put_email_to_pop3_server(self, port, email):
        m = MailBoxManagement(port, logger=logger)
        m.deliver_mail(pop3_account, open(email, 'r').read())

    def stop_pop3_server(self, port=None):
        if port:
            if self.my_mail_servers.get(str(port), None):
                process = self.my_mail_servers[str(port)]
                process.terminate()
                process.join()
            logger.info("POP3 Server (%s): stopped" % port)

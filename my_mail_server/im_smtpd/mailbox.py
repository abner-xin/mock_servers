import os
import uuid
import time
import glob
import shutil
import hashlib
import mock_logger


class MailBoxManagement:
    def __init__(self, port, logger=None):
        self.mailbox_root = os.path.join(os.getcwd(), "temp", 'mailbox_%s' % port)
        if not os.path.isdir(self.mailbox_root):
            os.mkdir(self.mailbox_root)
        self.logger = logger or mock_logger.logger

    @classmethod
    def get_all_mailboxes(cls):
        mailbox_root = os.path.join(os.getcwd(), "temp")
        return glob.glob(mailbox_root+r'\mailbox_*')

    @classmethod
    def clear_all_mailboxes(cls):
        for mailbox in cls.get_all_mailboxes():
            shutil.rmtree(mailbox)
            mock_logger.logger.info("cleared mailbox: %s" % mailbox)
        mock_logger.logger.info("cleared all mailboxes.")

    def _get_mailbox_path_for_recipient(self, recipient):
        local, domain = recipient.split('@')
        path_list = []
        path_list.append("%s__%s" % (domain[:20], hashlib.md5(domain).hexdigest()[:3])) # case-sensitive
        path_list.append("%s__%s" % (local[:20], hashlib.md5(local).hexdigest()[:3])) # case-sensitive
        return path_list

    def get_mailbox(self, recipient):
        mailbox_path = self.mailbox_root
        for path in self._get_mailbox_path_for_recipient(recipient):
            mailbox_path = os.path.join(mailbox_path, path)
            if not os.path.isdir(mailbox_path):
                os.mkdir(mailbox_path)
                self.logger.info("created path: %s" % mailbox_path)
        return mailbox_path

    def clear_mailbox(self, recipient=None):
        if recipient:
            shutil.rmtree(self.get_mailbox(recipient))
            self.logger.info("cleared emails for %s" % recipient)
        else:
            if os.path.exists(self.mailbox_root):
                shutil.rmtree(self.mailbox_root)
            self.logger.info('cleared all emails')

    def deliver_mail(self, recipient, mail_content):
        try:
            email_filename = "%s.eml" % uuid.uuid4()
            email_file = os.path.join(self.get_mailbox(recipient), email_filename)
            with open(email_file, 'w') as f:
                f.write(mail_content)
        except Exception, err:
            self.logger.info("Exception when deliver mail: %s" % err)
        else:
            self.logger.info("mail for %s is saved: %s" % (recipient, email_file))

    def get_mail(self, recipient):
        return glob.glob("%s/*.eml" % self.get_mailbox(recipient))

    def get_mail_from_mailbox(self, recipient, number=1, timeout=30):
        mailbox = self.get_mailbox(recipient)
        for sec in xrange(int(timeout)):
            mails = glob.glob("%s/*.eml" % mailbox)
            mail_number = len(mails)
            self.logger.info("%d emails are found" % mail_number)
            if mail_number == int(number):
                return mails
            elif mail_number > int(number):
                raise AssertionError("more than [%d] emails are found" % mail_number)
            else:
                time.sleep(1)

        raise AssertionError('Timeout')

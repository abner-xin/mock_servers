import mock_logger


class CredentialValidator(object):
    def __init__(self, logger=None):
        self._data = {}
        self.logger = logger or mock_logger.logger

    def add_one_account(self, username, password):
        self._data[username] = password

    def update(self, d):
        self._data.update(d)

    def validate(self, username, password):

        try:
            password_exp = self._data[username]
        except KeyError:
            self.logger.warn("user [%s] not exist" % username)
            return False

        if password_exp == password:
            self.logger.info("user [%s] is authenticated successfully" % username)
            return True
        else:
            self.logger.warn("user [%s] is authenticated failure" % username)
            return False
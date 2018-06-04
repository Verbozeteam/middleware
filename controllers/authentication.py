from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG

import os

class ControllerAuthentication:
    ALLOWED_TOKENS = None

    @staticmethod
    def initialize():
        if os.path.isfile(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE):
            with open(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE, "r") as F:
                content = F.read()
            content = content.replace('\r\n', '\n')
            lines = content.split('\n')
            ControllerAuthentication.ALLOWED_TOKENS = list(filter(lambda l: len(l) > 0, lines))
            Log.info("Loaded allowed tokens from {}".format(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE))

    @staticmethod
    def authenticate(controller, authentication_object):
        if ControllerAuthentication.ALLOWED_TOKENS == None:
            controller.is_authenticated = True
        else:
            token = authentication_object.get("token", None)
            password = authentication_object.get("password", None)
            if token and token in ControllerAuthentication.ALLOWED_TOKENS:
                controller.is_authenticated = True
            elif token and password and ControllerAuthentication.is_password_correct(password):
                ControllerAuthentication.register_token(token)
                controller.is_authenticated = True

        Log.debug("Controller {} authentication {}".format(str(controller), "successful" if controller.is_authenticated else "unsuccessful"))

    @staticmethod
    def is_password_correct(password):
        return password == CONTROLLERS_CONFIG.MASTER_PASSWORD_HASH

    @staticmethod
    def register_token(token):
        ControllerAuthentication.ALLOWED_TOKENS.append(token)
        if os.path.isfile(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE):
            with open(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE, "w") as F:
                F.write('\n'.join(ControllerAuthentication.ALLOWED_TOKENS))


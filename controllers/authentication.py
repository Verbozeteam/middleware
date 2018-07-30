from logs import Log
from config.controllers_config import CONTROLLERS_CONFIG

import os
import json
import hashlib

class TOKEN_TYPE:
    CONTROLLER = 1                 # Used by controllers to control Things
    HUB = 2                        # Used by a hub to connect this middleware to the internet
    UTILITY = 3                    # Used by middleware utilities that need to interact with the middleware (e.g. a logging service, status checker, ...)
    REMOTE_HARDWARE_CONTROLLER = 4 # Used by e.g. wireless ESP modules that can have sensors or actuators

class USER(object):
    Anonymous = None

    def __init__(self, token="", username="Anonymous", token_type=TOKEN_TYPE.CONTROLLER):
        self.username = username
        self.token = token
        self.token_type = token_type

    def __str__(self):
        return json.dumps({
            "username": self.username,
            "token": self.token,
            "token_type": self.token_type
        })

USER.Anonymous = USER()

class ControllerAuthentication:
    ALLOWED_TOKENS = None

    @staticmethod
    def initialize():
        if os.path.isfile(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE):
            with open(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE, "r") as F:
                content = json.load(F)
            ControllerAuthentication.ALLOWED_TOKENS = {}
            for user in content.values():
                ControllerAuthentication.ALLOWED_TOKENS[user["token"]] = USER(**user)
            Log.info("Loaded allowed tokens from {}".format(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE))
        else:
            Log.warning("All connections will be authenticated automatically (no tokens file provided)")
        if not CONTROLLERS_CONFIG.MASTER_PASSWORD_HASH:
            Log.warning("No master password hash provided")

    @staticmethod
    def authenticate(controller, authentication_object):
        if ControllerAuthentication.ALLOWED_TOKENS == None:
            controller.authenticated_user = USER.Anonymous
        else:
            token = authentication_object.get("token", None)
            password = authentication_object.get("password", None)
            username = authentication_object.get("username", "Registered User")
            token_type = authentication_object.get("token_type", TOKEN_TYPE.CONTROLLER)
            if token and token in ControllerAuthentication.ALLOWED_TOKENS:
                controller.authenticated_user = ControllerAuthentication.ALLOWED_TOKENS[token]
            elif token and password and ControllerAuthentication.is_password_correct(password):
                user = USER(token=token, username=username, token_type=token_type)
                ControllerAuthentication.register_user(user)
                controller.authenticated_user = user

        if controller.authenticated_user:
            controller.manager.on_controller_authenticated(controller)

        Log.debug("Controller {} authentication {}".format(str(controller), "successful" if controller.authenticated_user != None else "unsuccessful"))

    @staticmethod
    def is_password_correct(password):
        try:
            hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return hashed == CONTROLLERS_CONFIG.MASTER_PASSWORD_HASH
        except:
            return False

    @staticmethod
    def register_user(user):
        ControllerAuthentication.ALLOWED_TOKENS[user.token] = user
        if os.path.isfile(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE):
            with open(CONTROLLERS_CONFIG.ALLOWED_TOKENS_FILE, "w") as F:
                json.dump(dict(map(lambda u: (u.token, json.loads(str(u))), ControllerAuthentication.ALLOWED_TOKENS.values())), F)


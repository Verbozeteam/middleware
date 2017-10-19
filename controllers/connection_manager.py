from logs import Log

#
# Base class for a connection manager
# A connection manager is responsible for managing controllers connecting
# using a certain method (e.g. socket IO, Http server, etc...)
#
class ConnectionManager(object):
    def __init__(self, controllers_manager):
        self.controllers_manager = controllers_manager

    def update(self, cur_time_s):
        pass

    def cleanup(self):
        pass
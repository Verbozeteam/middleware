from core.select_service import Selectible
from logs import Log

import json

class Controller(Selectible):
    def __init__(self, controllers_manager, origin_name):
        self.manager = controllers_manager
        self.origin_name = origin_name
        self.authenticated_user = None
        self.manager.register_controller(self)
        self.cache = {} # thing_id -> thing state
        self.things_listening = [] # a list of things this Controller listens to (None means all)
        self.things_listening = None # set to [] then to None to fool the linter
        Log.info("Controller connected: {}".format(str(self)))

    def destroy_selectible(self):
        super(Controller, self).destroy_selectible()
        self.manager.deregister_controller(self)
        Log.info("Controller disconnected: {}".format(str(self)))

    # Called for a periodic update
    def update(self, cur_time_s):
        if not self.authenticated_user:
            return True

        try:
            my_things = self.manager.core.blueprint.get_things()
            if self.things_listening != None:
                my_things = filter(lambda t: t.id in self.things_listening, my_things)

            big_update = {}
            for thing in my_things:
                state = thing.get_state()
                state["token"] = thing.last_change_token
                if not thing.id in self.cache or not self.check_equal(self.cache[thing.id], state):
                    big_update[thing.id] = state
                    big_update[thing.id]["token"] = thing.last_change_token

            if big_update != {}:
                Log.hammoud("Controller::update(): [{}] sending {}".format(str(self), big_update))
                self.send_data(big_update)

        except:
            Log.error("Controller::update() Failed", exception=True)
            return False
        return True

    # Checks if the two objects are equal in actual value
    # obj1     Anything
    # obj2     Anything
    # returns  True iff obj1 and obj2 have the same VALUE (objects in python could be the same in value but will be different pointers)
    def check_equal(self, obj1, obj2):
        return obj1 == obj2 # @TODO: FIX EQUALITY?
        # if type(obj1) != type(obj2):
        #     return False
        # elif type(obj1) == type({}):
        #     return obj1 == obj2
        # else:
        #     return obj1 == obj2

    # Sends a JSON object to the controller
    # json_data  JSON data to send to the controller
    # cache      Whether or not to cache this data
    def send_data(self, json_data, cache=True):
        if cache:
            self.cache.update(json.loads(json.dumps(json_data))) # update the cache
        return True

    # Called when the controller sends a command
    # command  JSON command sent by the controller
    def on_command(self, command):
        self.manager.on_command(self, command)

    # Invalidates the cache
    # thing_id  ID of the thing to invalidate its cache entry. If None then all cache is cleared
    def invalidate_cache(self, thing_id=None):
        if thing_id == None: # invalidate entire cache
            self.cache = {}
        else:
            if thing_id in self.cache:
                del self.cache[thing_id]



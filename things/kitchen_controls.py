from things.thing import Thing
from logs import Log
import json
from functools import reduce

#
# Each order is of the following format:
# order = {
#   "id": INT, // order ID
#   "placed_by_name": STRING, // name of the orderer
#   "timeout": FLOAT, // time before its removed (internal use only)
#   "items": [{
#       "name": STRING,
#       "quantity": INT,
#       "status": INT, // -1 placed, 1 accepted, 0 rejected
#       "id": INT
#   }]
# }
#
# Menu of kitchen is of the following format:
# menu = [{
#   "name": STRING
# }]
#

class KitchenControls(Thing):
    def __init__(self, blueprint, kitchen_json):
        super(KitchenControls, self).__init__(blueprint, kitchen_json)
        self.id = "kitchen"
        self.orders = []
        if not hasattr(self, "menu"):
            self.menu = []
        self.id_generator = 1

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "kitchen_controls"

    def set_state(self, data, token_from):
        super(KitchenControls, self).set_state(data, token_from)
        if "order" in data and "placed_by_name" in data and\
            type(data["order"]) is list and len(data["order"]) > 0 and\
            (reduce(lambda x, y: x and y,\
                map(lambda i: "name" in i and type(i["name"]) is str and "quantity" in i and type(i["quantity"]) is int and i["quantity"] > 0, data["order"]))) and\
            type(data["placed_by_name"]) is str:

            for oi in data["order"]:
                oi["status"] = -1
                oi["id"] = self.id_generator
                self.id_generator += 1

            self.orders.append({
                "id": self.id_generator,
                "timeout": -1,
                "placed_by_name": data["placed_by_name"],
                "items": data["order"],
            })
            self.id_generator += 1
        if "accept" in data:
            for o in self.orders:
                for oi in o["items"]:
                    if oi["id"] == data["accept"]:
                        oi["status"] = 1
        if "reject" in data:
            for o in self.orders:
                for oi in o["items"]:
                    if oi["id"] == data["reject"]:
                        oi["status"] = 0
        return True # A lot of potential changes in the state

    def update(self, cur_time_s):
        for o in self.orders:
            if reduce(lambda x, y: x and y, map(lambda oi: oi["status"] != -1, o["items"])) and o["timeout"] < 0:
                o["timeout"] = cur_time_s + 10 # 60 seconds timeout

        L = len(self.orders)
        self.orders = list(filter(lambda o: o["timeout"] < 0 or o["timeout"] > cur_time_s, self.orders))
        self.dirty = self.dirty or L != len(self.orders)

    def get_state(self):
        return {
            "orders": self.orders,
            "menu": self.menu,
        }


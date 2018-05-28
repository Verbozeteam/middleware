from things.thing import Thing
from logs import Log
import json, datetime

class AlarmItem(object):
    CURRENT_ID = 1
    TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

    def __init__(self, data):
        self.id = AlarmItem.CURRENT_ID
        AlarmItem.CURRENT_ID += 1
        # example input format for time: 'Jun 1 2005  1:33PM'
        self.time = datetime.datetime.strptime(data["time"], AlarmItem.TIME_FORMAT)
        self.is_ringing = False

    def get_json(self):
        return {
            "id": self.id,
            "time": self.time.strftime(AlarmItem.TIME_FORMAT),
            "is_ringing": self.is_ringing
        }

class AlarmSystem(Thing):
    def __init__(self, blueprint, J):
        super(AlarmSystem, self).__init__(blueprint, J)
        self.id = J.get("id", "alarm")

        self.alarms = []

    @staticmethod
    def get_blueprint_tag():
        return "alarm_system"

    def get_state(self):
        return {
            "alarms": list(map(lambda a: a.get_json(), self.alarms)),
        }

    def set_state(self, data, token_from):
        super(AlarmSystem, self).set_state(data, token_from)

        if "add_alarm" in data:
            try:
                self.alarms.append(AlarmItem(data["add_alarm"]))
            except:
                Log.warning("Attempt to set alarm with invalid parameters", exception=True)
        if "remove_alarms" in data:
            self.alarms = list(filter(lambda a: a.id not in data["remove_alarms"], self.alarms))
        if "ring_alarm" in data:
            id = data["ring_alarm"]
            # remove any already ringing alarms
            self.alarms = list(filter(lambda a: not a.is_ringing or a.id == id, self.alarms))
            # ring the given alarm
            for i in range(0, len(self.alarms)):
                if self.alarms[i].id == id:
                    self.alarms[i].is_ringing = True

        return True
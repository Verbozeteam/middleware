from things.thing import Thing, ParamSpec, InputPortSpec, OutputPortSpec, GlobalSubParamSpec, ThingParams
from hardware.arduino_controller import ArduinoProtocol
from logs import Log
import json

# Base class for all states
class DiagnosticsState(object):
    def __init__(self):
        raise Exception("Needs to be overridden")
    # Returns None to continue the state, a new state object to go to the next state
    def update(self, report, cur_time_s):
        raise Exception("Needs to be overridden")

class DiagnosticsStateWait(DiagnosticsState):
    def __init__(self, wait_time_s, get_next_state_lambda):
        self.wait_time_s = wait_time_s
        self.start_time = -1
        self.get_next_state_lambda = get_next_state_lambda

    def update(self, report, cur_time_s):
        if (self.start_time < 0):
            self.start_time = cur_time_s
        if cur_time_s - self.start_time >= self.wait_time_s:
            return self.get_next_state_lambda()
        return None

class DiagnosticsStateInitialize(DiagnosticsState):
    def __init__(self, number_of_runs=0):
        self.number_of_runs = number_of_runs

    def update(self, report, cur_time_s):
        if self.number_of_runs >= 3:
            report.error(DiagnosticsReport.ERROR.FAILED_TO_INITIALIZE)
            return DiagnosticsStateFinalize()
        baseline = report.get_current_reading()
        is_initialized = self.number_of_runs > 0 and baseline != None
        Log.info("Running DiagnosticsStateInitialize (run {}, {})".format(self.number_of_runs, "initialized" if is_initialized else "still not initialized"))
        if not is_initialized:
            # on first run, turn off devices, set sensor to start reading
            # then wait 1 second and re-run this state with is_first_run=False
            report.begin_diagnostics()
            new_num_runs = self.number_of_runs + 1
            return DiagnosticsStateWait(1, lambda: DiagnosticsStateInitialize(new_num_runs))
        else:
            # already turned off devices and sensor should already be reading
            return DiagnosticsStateCheckThing(baseline)
        return None

class DiagnosticsStateCheckThing(DiagnosticsState):
    class STAGE:
        TURN_ON_THING = 0
        CHECK_ON_READING_1 = 1
        CHECK_ON_READING_2 = 2
        CHECK_ON_READING_3 = 3
        CHECK_ON_FAILED = 4
        CHECK_OFF_READING_1 = 5
        CHECK_OFF_READING_2 = 6
        CHECK_OFF_READING_3 = 7
        CHECK_OFF_FAILED = 8

    def __init__(self, baseline, stage=STAGE.TURN_ON_THING):
        self.baseline = baseline
        self.stage = stage

    def get_current_thing(self, report, remove=False):
        # first, get a light
        if len(report.lights) > 0:
            if remove:
                report.lights = report.lights[1:]
            else:
                return report.lights[0]
        return None

    def turn_on_thing(self, thing):
        Log.info("Turning on {}".format(thing.name))
        thing.set_intensity(100)

    def turn_off_thing(self, thing):
        Log.info("Turning off {}".format(thing.name))
        thing.set_intensity(0)

    def update(self, report, cur_time_s):
        thing = self.get_current_thing(report)
        next_stage = self.stage + 1
        wait_time = 1
        if not thing: # we are done
            return DiagnosticsStateFinalize()
        if self.stage == DiagnosticsStateCheckThing.STAGE.TURN_ON_THING:
            # get the Thing we want to check first
            self.turn_on_thing(thing)
        elif self.stage in [DiagnosticsStateCheckThing.STAGE.CHECK_ON_READING_1,
                            DiagnosticsStateCheckThing.STAGE.CHECK_ON_READING_2,
                            DiagnosticsStateCheckThing.STAGE.CHECK_ON_READING_3]:
            reading = report.get_current_reading()
            if reading != None and reading > self.baseline + 3:
                self.turn_off_thing(thing)
                next_stage = DiagnosticsStateCheckThing.STAGE.CHECK_OFF_READING_1
        elif self.stage in [DiagnosticsStateCheckThing.STAGE.CHECK_OFF_READING_1,
                            DiagnosticsStateCheckThing.STAGE.CHECK_OFF_READING_2,
                            DiagnosticsStateCheckThing.STAGE.CHECK_OFF_READING_3]:
            reading = report.get_current_reading()
            if reading != None and reading <= self.baseline + 3:
                self.get_current_thing(report, remove=True)
                next_stage = 0
                wait_time = 0.5
        elif self.stage in [DiagnosticsStateCheckThing.STAGE.CHECK_ON_FAILED,
                            DiagnosticsStateCheckThing.STAGE.CHECK_OFF_FAILED]:
            self.turn_off_thing(thing)
            self.get_current_thing(report, remove=True)
            next_stage = 0
            wait_time = 0.5
            report.error(DiagnosticsReport.ERROR.LIGHT_BROKEN(thing.name))
        return DiagnosticsStateWait(wait_time, lambda: DiagnosticsStateCheckThing(self.baseline, next_stage))

class DiagnosticsStateFinalize(DiagnosticsState):
    def __init__(self):
        pass

    def update(self, report, cur_time_s):
        report.end_diagnostics()
        if len(report.errors) > 0:
            report.status = DiagnosticsReport.STATUS.ERROR
        else:
            report.status = DiagnosticsReport.STATUS.OK
        Log.info("Diagnostics finished with status {}".format("OK" if report.status == DiagnosticsReport.STATUS.OK else "ERROR"))
        return None

class DiagnosticsReport(object):
    class STATUS:
        OK      = 0
        IDLE    = 1
        RUNNING = 2
        ERROR   = 3

    class ERROR:
        LIGHT_BROKEN            = lambda name: {"error": "Light ({}) is malfunctioning".format(name)}
        ALREADY_RUNNING         = {"error": "Diagnostics are already running"}
        ROOM_OCCUPIED           = {"error": "Room is occupied"}
        FAILED_TO_INITIALIZE    = {"error": "Failed to start diagnostics (current sensor not reading)"}
        CONTROLLER_DISCONNECTED = {"error": "Hardware controller disconnected"}

    def error(self, err):
        Log.warning("Diagnostic error: {}".format(err["error"]))
        self.errors.append(err)

    def __init__(self, blueprint, diagnostics):
        self.blueprint = blueprint
        self.diagnostics_thing = diagnostics
        self.reset()

    def start(self, params):
        # - collect things to be diagnosed
        # - make sure room is not occupied (if possible)
        # - turn off all devices
        # - initialize sensor to read on-change
        # - initialize state machine to begin reading
        #   - record baseline reading (should be 0, but could be more, print warning)
        #   - turn things on then off one by one and see if it reads current
        #   - log all that
        # - put sensor back to lazy state
        if self.status == DiagnosticsReport.STATUS.RUNNING:
            return

        Log.info("Room diagnostics being initialized")

        self.reset()

        things = self.blueprint.get_things()
        for thing in things:
            bpt = thing.get_blueprint_tag()
            if bpt in ['light_switches', 'dimmers']:
                self.lights.append(thing)
            elif bpt in ['bells']:
                self.bells.append(thing)
            elif bpt in ['central_acs', 'split_acs']:
                self.manual_acs.append(thing)
            elif bpt in ['hotel_controls']:
                self.hotel_controls = thing

        if self.hotel_controls and self.hotel_controls.card_in:
            self.error(DiagnosticsReport.ERROR.ROOM_OCCUPIED)
            self.status = DiagnosticsReport.STATUS.ERROR
            return

        self.current_state = DiagnosticsStateInitialize()
        self.status = DiagnosticsReport.STATUS.RUNNING

    def begin_diagnostics(self):
        # turn off devices
        for light in self.lights:
            light.set_state({"intensity": 0})
        for bell in self.bells:
            bell.is_bell_ringing = 0
        for ac in self.manual_acs:
            pass

        # send message to Arduino telling it to set the sensor reading interval to on-change
        self.blueprint.core.hw_manager.special_command(ArduinoProtocol.create_register_pin_listener(self.diagnostics_thing.params.get("sensor_port"), 100))

        # make hotel controls in diagnostics mode
        if self.hotel_controls:
            self.hotel_controls.set_diagnostics_mode(1)

    def end_diagnostics(self):
        # send message to Arduino telling it to set the sensor reading interval to never
        self.blueprint.core.hw_manager.special_command(ArduinoProtocol.create_register_pin_listener(self.diagnostics_thing.params.get("sensor_port"), 100000))

        # leave diagnostics mode in hotel_controls
        if self.hotel_controls:
            self.hotel_controls.set_diagnostics_mode(0)

    def on_current_reading(self, reading):
        if self.status == DiagnosticsReport.STATUS.RUNNING:
            self.current_readings.append(reading)

    def get_current_reading(self):
        if len(self.current_readings) == 0:
            return None
        reading = self.current_readings[-1] # this is the latest reading
        self.current_readings = [] # clear readings
        return reading

    def reset(self):
        self.current_state = None
        self.current_readings = []
        self.hotel_controls = None
        self.lights = []
        self.bells = []
        self.manual_acs = []
        self.status = DiagnosticsReport.STATUS.IDLE
        self.errors = []

    def update(self, cur_time_s):
        if self.status == DiagnosticsReport.STATUS.RUNNING and self.current_state:
            if not self.blueprint.core.hw_manager.is_synced():
                self.error(DiagnosticsReport.ERROR.CONTROLLER_DISCONNECTED)
                self.status = DiagnosticsReport.STATUS.ERROR
                return False
            new_state = self.current_state.update(self, cur_time_s)
            if new_state:
                self.current_state = new_state
            return True
        return False

    def getJSON(self):
        return {
            "status": self.status,
            "errors": self.errors,
        }

class RoomDiagnostics(Thing):
    def __init__(self, blueprint, J):
        super(RoomDiagnostics, self).__init__(blueprint, J)
        self.params = ThingParams(J, [
            InputPortSpec("sensor_port", 100000, is_required=True), # Sensor reading port, big number to indicate that we don't want to read
        ])
        self.id = J.get("id", "room_diagnostics")

        self.input_ports = self.params.get_input_ports()
        self.output_ports = self.params.get_output_ports()

        self.report = DiagnosticsReport(blueprint, self)

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return "room_diagnostics"

    def set_state(self, data, token_from="system"):
        super(RoomDiagnostics, self).set_state(data, "system") # Never use user token
        if "start_diagnostics" in data:
            self.report.start(data["start_diagnostics"])
        if "clear_report" in data:
            self.report.reset()
        return False

    def set_hardware_state(self, port, value):
        super(RoomDiagnostics, self).set_hardware_state(port, value)
        if port == self.params.get("sensor_port"):
            self.report.on_current_reading(value)
        return False

    def update(self, cur_time_s):
        return self.report.update(cur_time_s)

    def get_state(self):
        return {
            "report": self.report.getJSON()
        }

    def get_hardware_state(self):
        return {
        }

    def get_metadata(self):
        return {
        }


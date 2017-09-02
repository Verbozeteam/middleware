from hardware.controller_base import HardwareController

#
# An Arduino controller
#
class ArduinoController(HardwareController):
    def __init__(self, comport):
        super(self.__class__, self).__init__(comport)

    #
    # To identify an arduino on a COM port, find "arduino" anywhere in the
    # hardware description
    #
    @staticmethod
    def identify(ports):
        ret = []
        for p in ports:
            for attr in dir(p):
                a = getattr(p, attr)
                if type(a) == type("") and "arduino" in a.lower():
                    ret.append(p.serial_number)
        return ret

from logs import Log

class Thing(object):
    def __init__(self):
        pass

    # Should return the key in the blueprint that this Thing captures
    @staticmethod
    def get_blueprint_tag():
        return ""

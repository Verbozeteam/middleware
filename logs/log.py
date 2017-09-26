from config.general_config import GENERAL_CONFIG
import traceback
import sys

#
# Verbosity level, from almost silent to most verbose
#
class VERBOZITY:
    FATAL = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    VERBOZE = 5
    HAMMOUD = 6

#
# Singleton class to facilitate logging
#
class Log(object):
    @staticmethod
    def log(log_level, *args, **kwargs):
        print_dump = kwargs.get("exception", False)
        if "exception" in kwargs: del kwargs["exception"]
        if log_level <= GENERAL_CONFIG.LOG_VERBOZITY:
            if print_dump: traceback.print_exc()
            print(*args, **kwargs)

    @staticmethod
    def fatal(*args, **kwargs):
        Log.log(VERBOZITY.FATAL, *args, **kwargs)
        sys.exit(0)

    @staticmethod
    def error(*args, **kwargs): Log.log(VERBOZITY.ERROR, *args, **kwargs)

    @staticmethod
    def warning(*args, **kwargs): Log.log(VERBOZITY.WARNING, *args, **kwargs)

    @staticmethod
    def info(*args, **kwargs): Log.log(VERBOZITY.INFO, *args, **kwargs)

    @staticmethod
    def debug(*args, **kwargs): Log.log(VERBOZITY.DEBUG, *args, **kwargs)

    @staticmethod
    def verboze(*args, **kwargs): Log.log(VERBOZITY.VERBOZE, *args, **kwargs)

    @staticmethod
    def hammoud(*args, **kwargs): Log.log(VERBOZITY.HAMMOUD, *args, **kwargs)

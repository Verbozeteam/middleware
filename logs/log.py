from config.general_config import GENERAL_CONFIG
import traceback
import os, sys
import re
import shutil

import logging
from logging.handlers import RotatingFileHandler

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

    @staticmethod
    def get_logger_level(level):
        return {
            VERBOZITY.FATAL: logging.CRITICAL,
            VERBOZITY.ERROR: logging.ERROR,
            VERBOZITY.WARNING: logging.WARNING,
            VERBOZITY.INFO: logging.INFO
        }.get(level, logging.DEBUG)

#
# Singleton class to facilitate logging
#
class Log(object):
    @staticmethod
    def log(log_level, *args, **kwargs):
        print_dump = kwargs.get("exception", False)
        if "exception" in kwargs: del kwargs["exception"]
        if log_level <= GENERAL_CONFIG.LOG_VERBOZITY:
            if print_dump:
                traceback.print_exc()
                Log.logger.exception(*args)
            if GENERAL_CONFIG.LOG_REGEX != None: # regex filter
                found = False
                for a in args:
                    if GENERAL_CONFIG.LOG_REGEX.match(a) != None:
                        found = True
                        break
                if not found:
                    return
            print(*args, **kwargs)

    @staticmethod
    def fatal(*args, **kwargs):
        Log.log(VERBOZITY.FATAL, *args, **kwargs)
        Log.logger.critical(*args)
        sys.exit(0)

    @staticmethod
    def error(*args, **kwargs):
        Log.log(VERBOZITY.ERROR, *args, **kwargs)
        Log.logger.error(*args)

    @staticmethod
    def warning(*args, **kwargs):
        Log.log(VERBOZITY.WARNING, *args, **kwargs)
        Log.logger.warning(*args)

    @staticmethod
    def info(*args, **kwargs):
        Log.log(VERBOZITY.INFO, *args, **kwargs)
        Log.logger.info(*args)

    @staticmethod
    def debug(*args, **kwargs):
        Log.log(VERBOZITY.DEBUG, *args, **kwargs)
        Log.logger.debug(*args)

    @staticmethod
    def verboze(*args, **kwargs):
        Log.log(VERBOZITY.VERBOZE, *args, **kwargs)
        Log.logger.debug(*args)

    @staticmethod
    def hammoud(*args, **kwargs):
        Log.log(VERBOZITY.HAMMOUD, *args, **kwargs)
        Log.logger.debug(*args)

    @staticmethod
    def initialize():
        try:
            Log.logger = logging.getLogger('middleware')
            Log.logger.setLevel(VERBOZITY.get_logger_level(GENERAL_CONFIG.LOG_VERBOZITY))

            if not os.path.exists("log_files"):
                os.makedirs("log_files")
            runs = os.listdir("log_files")
            sorted_runs = {} # run number -> folder name
            max_run_number = 0
            for run in runs:
                try:
                    m = re.search("run_([0-9]+)+", run)
                    max_run_number = max(max_run_number, int(m.groups()[0]))
                    sorted_runs[int(m.groups()[0])] = run
                except:
                    if run != ".." and run != ".":
                        try: os.remove(os.path.join("log_files", run))
                        except: pass
                        try: shutil.rmtree(os.path.join("log_files", run))
                        except: pass
            if len(sorted_runs.keys()) > GENERAL_CONFIG.LOG_NUM_RUNS:
                for run_num in list(sorted(sorted_runs.keys()))[:-GENERAL_CONFIG.LOG_NUM_RUNS-1]:
                    try: shutil.rmtree(os.path.join("log_files", sorted_runs[run_num]))
                    except: traceback.print_exc()
                    try: os.remove(os.path.join("log_files", sorted_runs[run_num]))
                    except: pass

            log_folder_name = "log_files/run_{}".format(max_run_number+1)
            os.makedirs(log_folder_name)
            hdlr = RotatingFileHandler(os.path.join(log_folder_name, "mw.log"), backupCount=GENERAL_CONFIG.LOG_NUM_FILES, maxBytes=GENERAL_CONFIG.LOG_MAX_FILESIZE) # 10MB total per run
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            Log.logger.addHandler(hdlr)
        except:
            Log.log(VERBOZITY.ERROR, "Failed to open logs!", exception=True)

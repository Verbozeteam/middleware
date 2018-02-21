#!/usr/bin/env python

import config.cmd_args

from logs import Log
from core.core import Core

if __name__ == '__main__':
    # Initialize and run the core
    Log.initialize()
    core = Core()
    try:
        core.run()
    except:
        Log.fatal("Fatal error in program: ", exception=True)
    core.cleanup()

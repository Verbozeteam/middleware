#!/usr/bin/env python

import config.cmd_args

from core.core import Core

if __name__ == '__main__':
    # Initialize and run the core
    core = Core()
    core.run()
    core.cleanup()

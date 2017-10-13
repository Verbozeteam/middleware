import argparse
from config import *
import os, sys
import re

# Only parse command line arguments if not running tests
if not hasattr(sys, '_called_from_test'):
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Middleware core')
    parser.add_argument("-v", "--verbozity", required=False, type=int, help="Logging verbozity level")
    parser.add_argument("-b", "--blueprint", required=False, type=str, help="Building configuration file")
    parser.add_argument("-a", "--address", required=False, type=str, help="Socket server binding IP")
    parser.add_argument("-p", "--port", required=False, type=int, help="Socket server binding port")
    parser.add_argument("-s", "--simulate", action='store_true', required=False, help="Use fake serial communication to talk to arduino on socket (localhost, 9911)")
    parser.add_argument("-r", "--regex", required=False, type=str, help="Only print logging messages that match this regex")
    parser.add_argument("-i", "--interfaces", required=False, nargs='+', help="List of network interfaces to host sockets on")
    cmd_args = parser.parse_args()

    if cmd_args.verbozity: GENERAL_CONFIG.LOG_VERBOZITY = cmd_args.verbozity
    if cmd_args.regex: GENERAL_CONFIG.LOG_REGEX = re.compile(cmd_args.regex)
    if cmd_args.blueprint: GENERAL_CONFIG.BLUEPRINT_FILENAME = cmd_args.blueprint
    if cmd_args.address: CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_IP = cmd_args.address
    if cmd_args.port: CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT = cmd_args.port
    if cmd_args.interfaces: CONTROLLERS_CONFIG.SOCKET_HOSTING_INTERCACES = list(cmd_args.interfaces)

    if cmd_args.simulate: GENERAL_CONFIG.SIMULATE_ARDUINO = True

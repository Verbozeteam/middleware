import argparse
from config import *

# Parse command line arguments
parser = argparse.ArgumentParser(description='Middleware core')
parser.add_argument("-v", "--verbozity", required=False, type=int, help="Logging verbozity level")
parser.add_argument("-b", "--blueprint", required=False, type=str, help="Building configuration file")
parser.add_argument("-a", "--address", required=False, type=str, help="Socket server binding IP")
parser.add_argument("-p", "--port", required=False, type=int, help="Socket server binding port")
cmd_args = parser.parse_args()

if cmd_args.verbozity: GENERAL_CONFIG.LOG_VERBOZITY = cmd_args.verbozity
if cmd_args.blueprint: GENERAL_CONFIG.BLUEPRINT_FILENAME = cmd_args.blueprint
if cmd_args.address: CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_IP = cmd_args.address
if cmd_args.port: CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT = cmd_args.port

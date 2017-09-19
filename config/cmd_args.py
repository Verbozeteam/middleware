import argparse
from config import *

# Parse command line arguments
parser = argparse.ArgumentParser(description='Middleware core')
parser.add_argument("-b", "--blueprint", required=False, type=str, help="Building configuration file")
parser.add_argument("-ip", "--bind_ip", required=False, type=str, help="Socket server binding IP")
parser.add_argument("-port", "--bind_port", required=False, type=int, help="Socket server binding port")
cmd_args = parser.parse_args()

if cmd_args.blueprint: GENERAL_CONFIG.BLUEPRINT_FILENAME = cmd_args.blueprint
if cmd_args.bind_ip: CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_IP = cmd_args.bind_ip
if cmd_args.bind_port: CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT = cmd_args.bind_port

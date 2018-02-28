import argparse
import config
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
    parser.add_argument("-c", "--colors", required=False, action='store_true', help="enable printing colored logs")
    parser.add_argument("-d", "--disable", required=False, action='store_true', help="Disables connecting to hardware")
    parser.add_argument("-sp", "--serial-ports", required=False, type=str, help='Define serial ports to override system default enumeration. Format: \'<vendor>:<device_filename>,<vendor>:<device_filename>,...\' where <vendor> is used to determine which controller to assign the device (\'arduino\' for Arduino, \'FT231X USB UART\' for Zigbee) and <device> is the linux device path (e.g. \'/dev/ttyS0\')')
    cmd_args = parser.parse_args()

    if cmd_args.verbozity: config.GENERAL_CONFIG.LOG_VERBOZITY = cmd_args.verbozity
    if cmd_args.regex: config.GENERAL_CONFIG.LOG_REGEX = re.compile(cmd_args.regex)
    if cmd_args.blueprint: config.GENERAL_CONFIG.BLUEPRINT_FILENAME = cmd_args.blueprint
    if cmd_args.address: config.CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_IP = cmd_args.address
    if cmd_args.port: config.CONTROLLERS_CONFIG.SOCKET_SERVER_BIND_PORT = cmd_args.port
    if cmd_args.interfaces: config.CONTROLLERS_CONFIG.SOCKET_HOSTING_INTERCACES = list(cmd_args.interfaces)
    if cmd_args.colors: config.GENERAL_CONFIG.LOG_COLORS = True
    if cmd_args.disable: config.HARDWARE_CONFIG.DISABLE_HARDWARE = True
    if cmd_args.serial_ports: config.HARDWARE_CONFIG.SERIAL_PORTS = cmd_args.serial_ports

    if cmd_args.simulate: config.GENERAL_CONFIG.SIMULATE_ARDUINO = True

#!/usr/bin/python

import argparse
import os, sys
import re

parser = argparse.ArgumentParser(description='Ardunio emulator initializer')
parser.add_argument('-e', '--emulator_dir', required=True, help='<Required> Path to the Arduino emulator source (must contain run_emulator.sh and a custom_protocol.proto file)')
parser.add_argument('-b', '--board', help='Board name to emulate (default is mega2560)', default="mega2560")
cmd_args = parser.parse_args()

proto_path = cmd_args.emulator_dir
proto_filename = "custom_protocol.proto"
os.system("python -m grpc_tools.protoc -I{} --python_out=. --grpc_python_out=. {}".format(proto_path, proto_filename))
with open("custom_protocol_pb2_grpc.py", "r") as F:
    text = F.read()
m = re.search("import (.+)_pb2 as (.+)__pb2", text)
text = text.replace(m.group(0), m.group(0).replace("import ", "import testing_utils."))
with open("custom_protocol_pb2_grpc.py", "w") as F:
    F.write(text)

os.system("cd {} && ./run_emulator.sh {}".format(cmd_args.emulator_dir, cmd_args.board))

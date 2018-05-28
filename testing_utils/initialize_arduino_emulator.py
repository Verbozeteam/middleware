#!/usr/bin/python

import argparse
import os, sys
import re
from multiprocessing import Pool

parser = argparse.ArgumentParser(description='Ardunio emulator initializer')
parser.add_argument('-e', '--emulator_dir', required=True, help='<Required> Path to the Arduino emulator source (must contain run_emulator.sh and a custom_protocol.proto file)')
cmd_args = parser.parse_args()

rpc_port_1 = 5001
rpc_port_2 = 5002

serial_port_1 = 9911
serial_port_2 = 9920

time_multiplier_1 = 2.0
time_multiplier_2 = 5.0

proto_path = cmd_args.emulator_dir
proto_filename = "custom_protocol.proto"
os.system("python -m grpc_tools.protoc -I{} --python_out=. --grpc_python_out=. {}".format(proto_path, proto_filename))
with open("custom_protocol_pb2_grpc.py", "r") as F:
    text = F.read()
m = re.search("import (.+)_pb2 as (.+)__pb2", text)
text = text.replace(m.group(0), m.group(0).replace("import ", "import testing_utils."))
with open("custom_protocol_pb2_grpc.py", "w") as F:
    F.write(text)

p = Pool(2)
p.map(os.system, [
    "cd {} && ./run_emulator.sh mega2560 {} {} {}".format(cmd_args.emulator_dir, rpc_port_1, serial_port_1, time_multiplier_1),
    "cd {} && ./run_emulator.sh legacy {} {} {} 1".format(cmd_args.emulator_dir, rpc_port_2, serial_port_2, time_multiplier_2),
])

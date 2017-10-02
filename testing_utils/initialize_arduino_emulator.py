import argparse
import os, sys
import re

parser = argparse.ArgumentParser(description='Ardunio emulator initializer')
parser.add_argument('-p', '--protocol', help='Filename to the Ardunio RPC protocol')
cmd_args = parser.parse_args()

if cmd_args.protocol:
    (proto_path, proto_filename) = os.path.split(cmd_args.protocol)
    os.system("python -m grpc_tools.protoc -I{} --python_out=. --grpc_python_out=. {}".format(proto_path, proto_filename))
    with open("arduino_protocol_pb2_grpc.py", "r") as F:
        text = F.read()
    m = re.search("import (.+)_pb2 as (.+)__pb2", text)
    if m:
        text = text.replace(m.group(0), m.group(0).replace("import ", "import testing_utils."))
    with open("arduino_protocol_pb2_grpc.py", "w") as F:
        F.write(text)


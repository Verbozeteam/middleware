# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: arduino_protocol.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='arduino_protocol.proto',
  package='shammam',
  syntax='proto3',
  serialized_pb=_b('\n\x16\x61rduino_protocol.proto\x12\x07shammam\"\"\n\x03Pin\x12\x0c\n\x04type\x18\x01 \x01(\x05\x12\r\n\x05index\x18\x02 \x01(\x05\"\x16\n\x05State\x12\r\n\x05state\x18\x01 \x01(\x05\"9\n\x0bPinAndState\x12\x0c\n\x04type\x18\x01 \x01(\x05\x12\r\n\x05index\x18\x02 \x01(\x05\x12\r\n\x05state\x18\x03 \x01(\x05\"\x07\n\x05\x45mpty2\x9e\x01\n\x07\x41rduino\x12-\n\x0bGetPinState\x12\x0c.shammam.Pin\x1a\x0e.shammam.State\"\x00\x12\x35\n\x0bSetPinState\x12\x14.shammam.PinAndState\x1a\x0e.shammam.State\"\x00\x12-\n\tResetPins\x12\x0e.shammam.Empty\x1a\x0e.shammam.Empty\"\x00\x62\x06proto3')
)




_PIN = _descriptor.Descriptor(
  name='Pin',
  full_name='shammam.Pin',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='shammam.Pin.type', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='index', full_name='shammam.Pin.index', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=35,
  serialized_end=69,
)


_STATE = _descriptor.Descriptor(
  name='State',
  full_name='shammam.State',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='state', full_name='shammam.State.state', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=71,
  serialized_end=93,
)


_PINANDSTATE = _descriptor.Descriptor(
  name='PinAndState',
  full_name='shammam.PinAndState',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='shammam.PinAndState.type', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='index', full_name='shammam.PinAndState.index', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='state', full_name='shammam.PinAndState.state', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=95,
  serialized_end=152,
)


_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='shammam.Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=154,
  serialized_end=161,
)

DESCRIPTOR.message_types_by_name['Pin'] = _PIN
DESCRIPTOR.message_types_by_name['State'] = _STATE
DESCRIPTOR.message_types_by_name['PinAndState'] = _PINANDSTATE
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Pin = _reflection.GeneratedProtocolMessageType('Pin', (_message.Message,), dict(
  DESCRIPTOR = _PIN,
  __module__ = 'arduino_protocol_pb2'
  # @@protoc_insertion_point(class_scope:shammam.Pin)
  ))
_sym_db.RegisterMessage(Pin)

State = _reflection.GeneratedProtocolMessageType('State', (_message.Message,), dict(
  DESCRIPTOR = _STATE,
  __module__ = 'arduino_protocol_pb2'
  # @@protoc_insertion_point(class_scope:shammam.State)
  ))
_sym_db.RegisterMessage(State)

PinAndState = _reflection.GeneratedProtocolMessageType('PinAndState', (_message.Message,), dict(
  DESCRIPTOR = _PINANDSTATE,
  __module__ = 'arduino_protocol_pb2'
  # @@protoc_insertion_point(class_scope:shammam.PinAndState)
  ))
_sym_db.RegisterMessage(PinAndState)

Empty = _reflection.GeneratedProtocolMessageType('Empty', (_message.Message,), dict(
  DESCRIPTOR = _EMPTY,
  __module__ = 'arduino_protocol_pb2'
  # @@protoc_insertion_point(class_scope:shammam.Empty)
  ))
_sym_db.RegisterMessage(Empty)



_ARDUINO = _descriptor.ServiceDescriptor(
  name='Arduino',
  full_name='shammam.Arduino',
  file=DESCRIPTOR,
  index=0,
  options=None,
  serialized_start=164,
  serialized_end=322,
  methods=[
  _descriptor.MethodDescriptor(
    name='GetPinState',
    full_name='shammam.Arduino.GetPinState',
    index=0,
    containing_service=None,
    input_type=_PIN,
    output_type=_STATE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='SetPinState',
    full_name='shammam.Arduino.SetPinState',
    index=1,
    containing_service=None,
    input_type=_PINANDSTATE,
    output_type=_STATE,
    options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ResetPins',
    full_name='shammam.Arduino.ResetPins',
    index=2,
    containing_service=None,
    input_type=_EMPTY,
    output_type=_EMPTY,
    options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_ARDUINO)

DESCRIPTOR.services_by_name['Arduino'] = _ARDUINO

try:
  # THESE ELEMENTS WILL BE DEPRECATED.
  # Please use the generated *_pb2_grpc.py files instead.
  import grpc
  from grpc.beta import implementations as beta_implementations
  from grpc.beta import interfaces as beta_interfaces
  from grpc.framework.common import cardinality
  from grpc.framework.interfaces.face import utilities as face_utilities


  class ArduinoStub(object):
    # missing associated documentation comment in .proto file
    pass

    def __init__(self, channel):
      """Constructor.

      Args:
        channel: A grpc.Channel.
      """
      self.GetPinState = channel.unary_unary(
          '/shammam.Arduino/GetPinState',
          request_serializer=Pin.SerializeToString,
          response_deserializer=State.FromString,
          )
      self.SetPinState = channel.unary_unary(
          '/shammam.Arduino/SetPinState',
          request_serializer=PinAndState.SerializeToString,
          response_deserializer=State.FromString,
          )
      self.ResetPins = channel.unary_unary(
          '/shammam.Arduino/ResetPins',
          request_serializer=Empty.SerializeToString,
          response_deserializer=Empty.FromString,
          )


  class ArduinoServicer(object):
    # missing associated documentation comment in .proto file
    pass

    def GetPinState(self, request, context):
      # missing associated documentation comment in .proto file
      pass
      context.set_code(grpc.StatusCode.UNIMPLEMENTED)
      context.set_details('Method not implemented!')
      raise NotImplementedError('Method not implemented!')

    def SetPinState(self, request, context):
      # missing associated documentation comment in .proto file
      pass
      context.set_code(grpc.StatusCode.UNIMPLEMENTED)
      context.set_details('Method not implemented!')
      raise NotImplementedError('Method not implemented!')

    def ResetPins(self, request, context):
      # missing associated documentation comment in .proto file
      pass
      context.set_code(grpc.StatusCode.UNIMPLEMENTED)
      context.set_details('Method not implemented!')
      raise NotImplementedError('Method not implemented!')


  def add_ArduinoServicer_to_server(servicer, server):
    rpc_method_handlers = {
        'GetPinState': grpc.unary_unary_rpc_method_handler(
            servicer.GetPinState,
            request_deserializer=Pin.FromString,
            response_serializer=State.SerializeToString,
        ),
        'SetPinState': grpc.unary_unary_rpc_method_handler(
            servicer.SetPinState,
            request_deserializer=PinAndState.FromString,
            response_serializer=State.SerializeToString,
        ),
        'ResetPins': grpc.unary_unary_rpc_method_handler(
            servicer.ResetPins,
            request_deserializer=Empty.FromString,
            response_serializer=Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        'shammam.Arduino', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


  class BetaArduinoServicer(object):
    """The Beta API is deprecated for 0.15.0 and later.

    It is recommended to use the GA API (classes and functions in this
    file not marked beta) for all further purposes. This class was generated
    only to ease transition from grpcio<0.15.0 to grpcio>=0.15.0."""
    # missing associated documentation comment in .proto file
    pass
    def GetPinState(self, request, context):
      # missing associated documentation comment in .proto file
      pass
      context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)
    def SetPinState(self, request, context):
      # missing associated documentation comment in .proto file
      pass
      context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)
    def ResetPins(self, request, context):
      # missing associated documentation comment in .proto file
      pass
      context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)


  class BetaArduinoStub(object):
    """The Beta API is deprecated for 0.15.0 and later.

    It is recommended to use the GA API (classes and functions in this
    file not marked beta) for all further purposes. This class was generated
    only to ease transition from grpcio<0.15.0 to grpcio>=0.15.0."""
    # missing associated documentation comment in .proto file
    pass
    def GetPinState(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
      # missing associated documentation comment in .proto file
      pass
      raise NotImplementedError()
    GetPinState.future = None
    def SetPinState(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
      # missing associated documentation comment in .proto file
      pass
      raise NotImplementedError()
    SetPinState.future = None
    def ResetPins(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
      # missing associated documentation comment in .proto file
      pass
      raise NotImplementedError()
    ResetPins.future = None


  def beta_create_Arduino_server(servicer, pool=None, pool_size=None, default_timeout=None, maximum_timeout=None):
    """The Beta API is deprecated for 0.15.0 and later.

    It is recommended to use the GA API (classes and functions in this
    file not marked beta) for all further purposes. This function was
    generated only to ease transition from grpcio<0.15.0 to grpcio>=0.15.0"""
    request_deserializers = {
      ('shammam.Arduino', 'GetPinState'): Pin.FromString,
      ('shammam.Arduino', 'ResetPins'): Empty.FromString,
      ('shammam.Arduino', 'SetPinState'): PinAndState.FromString,
    }
    response_serializers = {
      ('shammam.Arduino', 'GetPinState'): State.SerializeToString,
      ('shammam.Arduino', 'ResetPins'): Empty.SerializeToString,
      ('shammam.Arduino', 'SetPinState'): State.SerializeToString,
    }
    method_implementations = {
      ('shammam.Arduino', 'GetPinState'): face_utilities.unary_unary_inline(servicer.GetPinState),
      ('shammam.Arduino', 'ResetPins'): face_utilities.unary_unary_inline(servicer.ResetPins),
      ('shammam.Arduino', 'SetPinState'): face_utilities.unary_unary_inline(servicer.SetPinState),
    }
    server_options = beta_implementations.server_options(request_deserializers=request_deserializers, response_serializers=response_serializers, thread_pool=pool, thread_pool_size=pool_size, default_timeout=default_timeout, maximum_timeout=maximum_timeout)
    return beta_implementations.server(method_implementations, options=server_options)


  def beta_create_Arduino_stub(channel, host=None, metadata_transformer=None, pool=None, pool_size=None):
    """The Beta API is deprecated for 0.15.0 and later.

    It is recommended to use the GA API (classes and functions in this
    file not marked beta) for all further purposes. This function was
    generated only to ease transition from grpcio<0.15.0 to grpcio>=0.15.0"""
    request_serializers = {
      ('shammam.Arduino', 'GetPinState'): Pin.SerializeToString,
      ('shammam.Arduino', 'ResetPins'): Empty.SerializeToString,
      ('shammam.Arduino', 'SetPinState'): PinAndState.SerializeToString,
    }
    response_deserializers = {
      ('shammam.Arduino', 'GetPinState'): State.FromString,
      ('shammam.Arduino', 'ResetPins'): Empty.FromString,
      ('shammam.Arduino', 'SetPinState'): State.FromString,
    }
    cardinalities = {
      'GetPinState': cardinality.Cardinality.UNARY_UNARY,
      'ResetPins': cardinality.Cardinality.UNARY_UNARY,
      'SetPinState': cardinality.Cardinality.UNARY_UNARY,
    }
    stub_options = beta_implementations.stub_options(host=host, metadata_transformer=metadata_transformer, request_serializers=request_serializers, response_deserializers=response_deserializers, thread_pool=pool, thread_pool_size=pool_size)
    return beta_implementations.dynamic_stub(channel, 'shammam.Arduino', cardinalities, options=stub_options)
except ImportError:
  pass
# @@protoc_insertion_point(module_scope)
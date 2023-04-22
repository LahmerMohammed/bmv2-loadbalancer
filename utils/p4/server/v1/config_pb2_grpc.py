# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from p4.server.v1 import config_pb2 as p4_dot_server_dot_v1_dot_config__pb2


class ServerConfigStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Set = channel.unary_unary(
                '/p4.server.v1.ServerConfig/Set',
                request_serializer=p4_dot_server_dot_v1_dot_config__pb2.SetRequest.SerializeToString,
                response_deserializer=p4_dot_server_dot_v1_dot_config__pb2.SetResponse.FromString,
                )
        self.Get = channel.unary_unary(
                '/p4.server.v1.ServerConfig/Get',
                request_serializer=p4_dot_server_dot_v1_dot_config__pb2.GetRequest.SerializeToString,
                response_deserializer=p4_dot_server_dot_v1_dot_config__pb2.GetResponse.FromString,
                )


class ServerConfigServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Set(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Get(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ServerConfigServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Set': grpc.unary_unary_rpc_method_handler(
                    servicer.Set,
                    request_deserializer=p4_dot_server_dot_v1_dot_config__pb2.SetRequest.FromString,
                    response_serializer=p4_dot_server_dot_v1_dot_config__pb2.SetResponse.SerializeToString,
            ),
            'Get': grpc.unary_unary_rpc_method_handler(
                    servicer.Get,
                    request_deserializer=p4_dot_server_dot_v1_dot_config__pb2.GetRequest.FromString,
                    response_serializer=p4_dot_server_dot_v1_dot_config__pb2.GetResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'p4.server.v1.ServerConfig', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ServerConfig(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Set(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/p4.server.v1.ServerConfig/Set',
            p4_dot_server_dot_v1_dot_config__pb2.SetRequest.SerializeToString,
            p4_dot_server_dot_v1_dot_config__pb2.SetResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Get(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/p4.server.v1.ServerConfig/Get',
            p4_dot_server_dot_v1_dot_config__pb2.GetRequest.SerializeToString,
            p4_dot_server_dot_v1_dot_config__pb2.GetResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import switchml_pb2 as switchml__pb2


class SessionStub(object):
    """Missing associated documentation comment in .proto file"""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RdmaSession = channel.unary_unary(
                '/switchml_proto.Session/RdmaSession',
                request_serializer=switchml__pb2.RdmaSessionRequest.SerializeToString,
                response_deserializer=switchml__pb2.RdmaSessionResponse.FromString,
                )
        self.UdpSession = channel.unary_unary(
                '/switchml_proto.Session/UdpSession',
                request_serializer=switchml__pb2.UdpSessionRequest.SerializeToString,
                response_deserializer=switchml__pb2.UdpSessionResponse.FromString,
                )


class SessionServicer(object):
    """Missing associated documentation comment in .proto file"""

    def RdmaSession(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UdpSession(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SessionServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RdmaSession': grpc.unary_unary_rpc_method_handler(
                    servicer.RdmaSession,
                    request_deserializer=switchml__pb2.RdmaSessionRequest.FromString,
                    response_serializer=switchml__pb2.RdmaSessionResponse.SerializeToString,
            ),
            'UdpSession': grpc.unary_unary_rpc_method_handler(
                    servicer.UdpSession,
                    request_deserializer=switchml__pb2.UdpSessionRequest.FromString,
                    response_serializer=switchml__pb2.UdpSessionResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'switchml_proto.Session', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Session(object):
    """Missing associated documentation comment in .proto file"""

    @staticmethod
    def RdmaSession(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/switchml_proto.Session/RdmaSession',
            switchml__pb2.RdmaSessionRequest.SerializeToString,
            switchml__pb2.RdmaSessionResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UdpSession(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/switchml_proto.Session/UdpSession',
            switchml__pb2.UdpSessionRequest.SerializeToString,
            switchml__pb2.UdpSessionResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)


class SyncStub(object):
    """Missing associated documentation comment in .proto file"""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Barrier = channel.unary_unary(
                '/switchml_proto.Sync/Barrier',
                request_serializer=switchml__pb2.BarrierRequest.SerializeToString,
                response_deserializer=switchml__pb2.BarrierResponse.FromString,
                )
        self.Broadcast = channel.unary_unary(
                '/switchml_proto.Sync/Broadcast',
                request_serializer=switchml__pb2.BroadcastRequest.SerializeToString,
                response_deserializer=switchml__pb2.BroadcastResponse.FromString,
                )


class SyncServicer(object):
    """Missing associated documentation comment in .proto file"""

    def Barrier(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Broadcast(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SyncServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Barrier': grpc.unary_unary_rpc_method_handler(
                    servicer.Barrier,
                    request_deserializer=switchml__pb2.BarrierRequest.FromString,
                    response_serializer=switchml__pb2.BarrierResponse.SerializeToString,
            ),
            'Broadcast': grpc.unary_unary_rpc_method_handler(
                    servicer.Broadcast,
                    request_deserializer=switchml__pb2.BroadcastRequest.FromString,
                    response_serializer=switchml__pb2.BroadcastResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'switchml_proto.Sync', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Sync(object):
    """Missing associated documentation comment in .proto file"""

    @staticmethod
    def Barrier(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/switchml_proto.Sync/Barrier',
            switchml__pb2.BarrierRequest.SerializeToString,
            switchml__pb2.BarrierResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Broadcast(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/switchml_proto.Sync/Broadcast',
            switchml__pb2.BroadcastRequest.SerializeToString,
            switchml__pb2.BroadcastResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

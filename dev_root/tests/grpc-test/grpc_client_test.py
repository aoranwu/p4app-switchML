# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the GRPC helloworld.Greeter client."""

from __future__ import print_function
import logging

import grpc

import switchml_pb2
import switchml_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50099') as channel:
        stub = switchml_pb2_grpc.SessionStub(channel)
        response = stub.UdpSession(switchml_pb2.UdpSessionRequest(
            session_id = 0,
            rank = 2,
            num_workers = 2,
            mac = 0xde08bed70147,
            ipv4= 0xc613c832,
            packet_size = 0,
            udp_port = 12345
        ))
        response = stub.UdpSession(switchml_pb2.UdpSessionRequest(
            session_id = 0,
            rank = 3,
            num_workers = 2,
            mac = 0x62681bcb1805,
            ipv4= 0xc613c831,
            packet_size = 0,
            udp_port = 12345
        ))
        response = stub.UdpSession(switchml_pb2.UdpSessionRequest(
            session_id = 0,
            rank = 4,
            num_workers = 2,
            mac = 0x86bd7b5cb92b,
            ipv4= 0xc613c830,
            packet_size = 0,
            udp_port = 12345
        ))
        response = stub.UdpSession(switchml_pb2.UdpSessionRequest(
            session_id = 0,
            rank = 1,
            num_workers = 2,
            mac = 0x7e0aaefb53df,
            ipv4= 0xc613c82f,
            packet_size = 0,
            udp_port = 12345
        ))
    print("Greeter client received: " + str(response.mac))


if __name__ == '__main__':
    logging.basicConfig()
    run()

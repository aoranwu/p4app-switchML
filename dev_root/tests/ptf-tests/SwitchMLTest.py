# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
This is the base class for testing SwitchML.

Much of the SwitchML configuration code is in the ../py directory; we
import that by having a symlink named SwitchML in this directory, so
that we can import from SwitchML.*.
"""

import unittest
import logging 
import grpc   
import pdb

import ptf
from ptf.testutils import *
from bfruntime_client_base_tests import BfRuntimeTest
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc

import os
import sys
import random

from pprint import pprint

from scapy.all import *

# import SwitchML job setup
from SwitchML.Job import Job
from SwitchML.Worker import Worker, WorkerType
from SwitchML.Packets import  make_switchml_rdma, rdma_opcode_s2n


class SwitchML(Packet):
    name = "SwitchML"
    fields_desc=[
        XBitField(     "msgType", 0, 4),
        XBitField(      "unused", 0, 1),
        XBitField(      "size", 0, 3),
        XBitField(      "job_number", 0, 8),
        XIntField(         "tsi", 0),
        XShortField("pool_index", 2),
        XShortField("original_worker_id",0)
    ]

class SwitchMLExponent(Packet):
    name = "SwitchMLExponent"
    fields_desc=[
        ShortField("e0", random.randint(0, 255))
    ]

class SwitchMLData(Packet):
    name = "SwitchMLData"
    fields_desc=[
        IntField("d0", 0),
        IntField("d1", 1),
        IntField("d2", 2),
        IntField("d3", 3),
        IntField("d4", 4),
        IntField("d5", 5),
        IntField("d6", 6),
        IntField("d7", 7),
        IntField("d8", 8),
        IntField("d9", 9),
        IntField("d10", 10),
        IntField("d11", 11),
        IntField("d12", 12),
        IntField("d13", 13),
        IntField("d14", 14),
        IntField("d15", 15),
        IntField("d16", 16),
        IntField("d17", 17),
        IntField("d18", 18),
        IntField("d19", 19),
        IntField("d20", 20),
        IntField("d21", 21),
        IntField("d22", 22),
        IntField("d23", 23),
        IntField("d24", 24),
        IntField("d25", 25),
        IntField("d26", 26),
        IntField("d27", 27),
        IntField("d28", 28),
        IntField("d29", 29),
        IntField("d30", 30),
        IntField("d31", 31),
    ]

class SwitchMLData64(Packet):
    name = "SwitchMLData64"
    fields_desc=[
        FieldListField("significands", [], SignedIntField("", 0), count_from=lambda pkt: 64)
    ]
    

def make_switchml_udp(src_mac, src_ip, dst_mac, dst_ip, src_port, dst_port, pool_index,
                      value_multiplier=1, checksum=None,worker_id=0):
    p = (Ether(dst=dst_mac, src=src_mac) /
         IP(dst=dst_ip, src=src_ip)/
         UDP(sport=src_port, dport=dst_port)/
         SwitchML(pool_index=pool_index,size=1,original_worker_id=worker_id) /
         SwitchMLData() /
         SwitchMLData() /
         SwitchMLExponent())  # TODO: move exponents before data once daiet code supports it

    # initialize data
    for i in range(32):
        setattr(p.getlayer('SwitchMLData', 1), 'd{}'.format(i), value_multiplier * i)
        setattr(p.getlayer('SwitchMLData', 2), 'd{}'.format(i), value_multiplier * (i+32))

    if checksum is not None:
        p['UDP'].chksum = checksum
        
    return p



# init logging
logger = logging.getLogger('Test')
if not len(logger.handlers):
    logger.addHandler(logging.StreamHandler())

# log at info level
logging.basicConfig(level=logging.INFO)


class SwitchMLTest(BfRuntimeTest):

    def setUp(self):
        self.client_id = 0
        self.p4_name   = "switchml"
        self.dev       = 0
        self.dev_tgt   = gc.Target(self.dev, pipe_id=0xFFFF)
        
        BfRuntimeTest.setUp(self, self.client_id, self.p4_name)
        
        self.bfrt_info = self.interface.bfrt_info_get()

        self.job = None

    def tearDown(self):
        self.cleanUp()
        BfRuntimeTest.tearDown(self)

    def cleanUp(self):
        try:
            if self.job is not None:
                self.job.clear_all()
        except Exception as e:
            print("Error cleaning up: {}".format(e))

    def make_switchml_packets(self, workers, pool_index, value_multiplier, dst_port, base_worker_id=0,switch_num=1):
        packets = []
        scaled_value_multiplier = value_multiplier * len(workers) *switch_num
        for i,w in enumerate(workers):
            if w.worker_type is WorkerType.SWITCHML_UDP:
                p = make_switchml_udp(src_mac=w.mac,
                                      src_ip=w.ip,
                                      dst_mac=self.switch_mac,
                                      dst_ip=self.switch_ip,
                                      src_port=w.udp_port,
                                      dst_port=dst_port,
                                      pool_index=pool_index,
                                      value_multiplier=value_multiplier,
                                      worker_id = base_worker_id+i
                                      )
                e = make_switchml_udp(src_mac=self.switch_mac,
                                      src_ip=self.switch_ip,
                                      dst_mac=w.mac,
                                      dst_ip=w.ip,
                                      src_port=dst_port,
                                      dst_port=w.udp_port,
                                      pool_index=pool_index,
                                      checksum=0,
                                      value_multiplier=scaled_value_multiplier,
                                      worker_id=i
                                      )
                packets.append( (p, e) )
            elif w.worker_type is WorkerType.ROCEv2:
                p = make_switchml_rdma(src_mac=w.mac, # TODO: make RDMA when ready
                                       src_ip=w.ip,
                                       dst_mac=self.switch_mac,
                                       dst_ip=self.switch_ip,
                                       src_port=0x1234,
                                       opcode=rdma_opcode_s2n['UC_RDMA_WRITE_ONLY_IMMEDIATE'],
                                       dst_qp=w.roce_base_qpn + pool_index,
                                       value_multiplier=value_multiplier)
                e = make_switchml_rdma(src_mac=self.switch_mac,
                                       src_ip=self.switch_ip,
                                       dst_mac=w.mac,
                                       dst_ip=w.ip,
                                       src_port=0x2345,
                                       opcode=rdma_opcode_s2n['UC_RDMA_WRITE_ONLY_IMMEDIATE'],
                                       dst_qp=w.roce_base_qpn + pool_index,
                                       value_multiplier=scaled_value_multiplier)
                packets.append( (p, e) )
            
        return tuple(packets)

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import time
import sys
import os
from pprint import pprint

import random

from ptf import config
from ptf.thriftutils import *
from ptf.testutils import *

from bfruntime_client_base_tests import BfRuntimeTest
import bfrt_grpc.client as gc

from scapy.all import *

# import SwitchML setup
from SwitchML.Job import Job
from SwitchML.Worker import Worker, WorkerType
from SwitchML.Packets import make_switchml_udp

# import SwitchML test base class
from SwitchMLTest import *

# init logging
logger = logging.getLogger('Test')
if not len(logger.handlers):
    logger.addHandler(logging.StreamHandler())

# log at info level
logging.basicConfig(level=logging.INFO)

first_worker_port = 0
second_worker_port = 4


class TwoWorkerTest(SwitchMLTest):
    """
    Base class for 2-worker SwitchML tests
    """

    def setUp(self):
        SwitchMLTest.setUp(self)
        
        # device ID: 0
        self.dev_id = 0

        # mac, ip, and udp port number that switch will respond to
        self.switch_mac           = "06:00:00:00:00:03"
        self.switch_ip            = "198.19.200.203"
        self.switch_udp_port      = 0xbee0
        self.switch_udp_port_mask = 0xfff0

        # need to change the mac address to upper case!!
        # self.all_workers = [
        #     # Two UDP workers
        #     Worker(mac="72:8b:45:3d:ee:fb".upper(), ip="198.19.200.49", udp_port=12345, front_panel_port=4, lane=0, speed=100, fec='none'),
        #     Worker(mac="4a:9c:bf:40:60:49".upper(), ip="198.19.200.48", udp_port=12345, front_panel_port=8, lane=0, speed=100, fec='none'),
        #     # # A non-SwitchML worker
        #     # Worker(mac="b8:83:03:74:01:c4", ip="198.19.200.48", front_panel_port=1, lane=2, speed=10, fec='none'),
        # ]

        self.all_workers = [
        Worker(mac="86:bd:7b:5c:b9:2b", ip="198.19.200.48", udp_port=12345, front_panel_port=17, lane=0, speed=100, fec='none'),
        Worker(mac="7e:0a:ae:fb:53:df", ip="198.19.200.47", udp_port=12345, front_panel_port=18, lane=0, speed=100, fec='none')
        ]
        self.switchml_workers = [w for w in self.all_workers if w.worker_type is not WorkerType.FORWARD_ONLY]
                                                                             
        # self.job = Job(gc, self.bfrt_info,
        #                self.switch_ip, self.switch_mac, self.switch_udp_port, self.switch_udp_port_mask, 
        #                self.all_workers)

        # make packets for set 0
        ((self.pktW0S0, self.expected_pktW0S0),
         (self.pktW1S0, self.expected_pktW1S0)) = self.make_switchml_packets(self.switchml_workers,
                                                                             0x0000, 1, self.switch_udp_port,base_worker_id=4,switch_num=2)

        # make packets for set 1
        ((self.pktW0S1, self.expected_pktW0S1),
         (self.pktW1S1, self.expected_pktW1S1)) = self.make_switchml_packets(self.switchml_workers,
                                                                             0x8000, 2, self.switch_udp_port)
        
        # make additional packets with different values to verify slot reuse
        ((self.pktW0S0x3, self.expected_pktW0S0x3),
         (self.pktW1S0x3, self.expected_pktW1S0x3)) = self.make_switchml_packets(self.switchml_workers,
                                                                                 0x0000, 6, self.switch_udp_port)
        ((self.pktW0S1x3, self.expected_pktW0S1x3),
         (self.pktW1S1x3, self.expected_pktW1S1x3)) = self.make_switchml_packets(self.switchml_workers,
                                                                                 0x8000, 6, self.switch_udp_port)

        # make packets for the next slot with different ports
        ((self.pktW0S0p1, self.expected_pktW0S0p1),
         (self.pktW1S0p1, self.expected_pktW1S0p1)) = self.make_switchml_packets(self.switchml_workers,
                                                                                 0x0001, 2, self.switch_udp_port+1)
        ((self.pktW0S1p1, self.expected_pktW0S1p1),
         (self.pktW1S1p1, self.expected_pktW1S1p1)) = self.make_switchml_packets(self.switchml_workers,
                                                                                 0x8001, 2, self.switch_udp_port+1)
        # self.pktW0S0p1['UDP'].sport          = self.pktW0S0p1['UDP'].sport + 1
        # self.pktW1S0p1['UDP'].sport          = self.pktW1S0p1['UDP'].sport + 1
        # self.pktW0S1p1['UDP'].sport          = self.pktW0S1p1['UDP'].sport + 1
        # self.pktW1S1p1['UDP'].sport          = self.pktW1S1p1['UDP'].sport + 1
        # self.expected_pktW0S0p1['UDP'].dport = self.expected_pktW0S0p1['UDP'].dport + 1
        # self.expected_pktW1S0p1['UDP'].dport = self.expected_pktW1S0p1['UDP'].dport + 1
        # self.expected_pktW0S1p1['UDP'].dport = self.expected_pktW0S1p1['UDP'].dport + 1
        # self.expected_pktW1S1p1['UDP'].dport = self.expected_pktW1S1p1['UDP'].dport + 1
 
        self.pktW0S0p1['UDP'].sport          = 0xbee0
        self.pktW1S0p1['UDP'].sport          = 0xbee0
        self.pktW0S1p1['UDP'].sport          = 0xbee0
        self.pktW1S1p1['UDP'].sport          = 0xbee0
        self.expected_pktW0S0p1['UDP'].dport = 0xbee0
        self.expected_pktW1S0p1['UDP'].dport = 0xbee0
        self.expected_pktW0S1p1['UDP'].dport = 0xbee0
        self.expected_pktW1S1p1['UDP'].dport = 0xbee0
 
 
class BasicReduction(TwoWorkerTest):
    """
    Test basic operation of a single slot.
    """

    def runTest(self):
        # do a straightforward reduction in the first slot
        self.pktW0S0.show()
        send_packet(self, 256, self.pktW0S0)

        # Ether(self.expected_pktW0S0).show()
        send_packet(self, 260, self.pktW1S0)
        self.expected_pktW0S0['SwitchML'].msgType=2
        self.expected_pktW1S0['SwitchML'].msgType=2
        self.expected_pktW1S0['SwitchML'].original_worker_id=1
        # self.expected_pktW0S0['SwitchML'].original_worker_id=1
        # verify_packet(self, self.expected_pktW0S0, 128)
        # verify_packet(self, self.expected_pktW1S0, 132)
        verify_packet(self, self.expected_pktW0S0, 256, timeout=5)
        verify_packet(self, self.expected_pktW0S0, 260, timeout=5)


class RetransmitAfterReduction(TwoWorkerTest):
    """
    Ensure we can retransmit from a slot after it has received all
    updates and before its paired slot has received its first update.

    """

    def runTest(self):
        # first do a straightforward reduction in the first set
        send_packet(self, first_worker_port, self.pktW0S0)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S0)

        verify_packet(self, self.expected_pktW0S0, first_worker_port)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # try retransmission from second worker
        send_packet(self, second_worker_port, self.pktW1S0)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # try retransmission from second worker again
        send_packet(self, second_worker_port, self.pktW1S0)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # try retransmission from second worker one more time
        send_packet(self, second_worker_port, self.pktW1S0)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # try retransmission from first worker
        send_packet(self, first_worker_port, self.pktW0S0)
        verify_packet(self, self.expected_pktW0S0, first_worker_port)

        # try retransmission from first worker again
        send_packet(self, first_worker_port, self.pktW0S0)
        verify_packet(self, self.expected_pktW0S0, first_worker_port)

class OtherSetReduction(TwoWorkerTest):
    """
    Test basic operation of a single slot, starting from the second
    set instead of the first.
    """

    def runTest(self):
        # do a straightforward reduction in the second set
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S1)

        verify_packet(self, self.expected_pktW0S1, first_worker_port)
        verify_packet(self, self.expected_pktW1S1, second_worker_port)

class BothSetsReduction(TwoWorkerTest):
    """
    Test basic operation of a pair of sets in a slot.
    """

    def runTest(self):
        # do a straightforward reduction in the first set
        send_packet(self, first_worker_port, self.pktW0S0)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S0)

        verify_packet(self, self.expected_pktW0S0, first_worker_port)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # now do a straightforward reduction in the second set
        send_packet(self, first_worker_port, self.pktW0S1x3)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S1x3)

        verify_packet(self, self.expected_pktW0S1x3, first_worker_port)
        verify_packet(self, self.expected_pktW1S1x3, second_worker_port)
        

class SlotReuse(TwoWorkerTest):
    """
    Test basic slot reuse.
    """

    def runTest(self):
        # do a straightforward reduction in the first set
        send_packet(self, first_worker_port, self.pktW0S0)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S0)

        verify_packet(self, self.expected_pktW0S0, first_worker_port)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # now do a straightforward reduction in the second set
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S1)

        verify_packet(self, self.expected_pktW0S1, first_worker_port)
        verify_packet(self, self.expected_pktW1S1, second_worker_port)
        
        # now reduce in first set again
        send_packet(self, first_worker_port, self.pktW0S0x3)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S0x3)

        verify_packet(self, self.expected_pktW0S0x3, first_worker_port)
        verify_packet(self, self.expected_pktW1S0x3, second_worker_port)

        # now reduce in second set again
        send_packet(self, first_worker_port, self.pktW0S1x3)
        verify_no_other_packets(self)

        send_packet(self, 1, self.pktW1S1x3)

        verify_packet(self, self.expected_pktW0S1x3, first_worker_port)
        verify_packet(self, self.expected_pktW1S1x3, second_worker_port)

class IgnoreRetransmissions(TwoWorkerTest):
    """
    Ensure that retransmissions during reduction are ignored.
    """

    def runTest(self):
        # half-complete reduction in set 1
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_no_other_packets(self)
        
        # make sure retransmissions to that set from the same worker are ignored
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_no_other_packets(self)

        send_packet(self, first_worker_port, self.pktW0S1)
        verify_no_other_packets(self)

        # now finish aggregation
        send_packet(self, second_worker_port, self.pktW1S1)

        # ensure that we still get the correct answer
        verify_packet(self, self.expected_pktW0S1, first_worker_port)
        verify_packet(self, self.expected_pktW1S1, second_worker_port)
        
class RetransmitFromPreviousSet(TwoWorkerTest):
    """
    Ensure that retransmissions to a previously-aggregated set generate replies.
    """

    def runTest(self):
        # start by doing a straightforward reduction in the second set
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S1)

        # check the answer
        verify_packet(self, self.expected_pktW0S1, first_worker_port)
        verify_packet(self, self.expected_pktW1S1, second_worker_port)

        # now, half-complete reduction in the first set
        send_packet(self, second_worker_port, self.pktW1S0x3)
        
        # verify we can still retransmit from the second set
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_packet(self, self.expected_pktW0S1, first_worker_port)

        # try again
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_packet(self, self.expected_pktW0S1, first_worker_port)

        # try again one more time
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_packet(self, self.expected_pktW0S1, first_worker_port)

        # ensure we get no other packets.
        verify_no_other_packets(self)

        
class SlotReuseAndRetransmit(TwoWorkerTest):
    """
    Test basic slot reuse.
    """

    def runTest(self):
        # do a straightforward reduction in the first set
        send_packet(self, first_worker_port, self.pktW0S0)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S0)

        verify_packet(self, self.expected_pktW0S0, first_worker_port)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # now do a straightforward reduction in the second set
        send_packet(self, first_worker_port, self.pktW0S1)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S1)

        verify_packet(self, self.expected_pktW0S1, first_worker_port)
        verify_packet(self, self.expected_pktW1S1, second_worker_port)
        
        # now reduce in first set again
        send_packet(self, first_worker_port, self.pktW0S0x3)
        verify_no_other_packets(self)
        
        send_packet(self, second_worker_port, self.pktW1S0x3)

        verify_packet(self, self.expected_pktW0S0x3, first_worker_port)
        verify_packet(self, self.expected_pktW1S0x3, second_worker_port)

        # now half-complete reduction in second set again
        send_packet(self, second_worker_port, self.pktW1S1x3)
        verify_no_other_packets(self)

        # and verify we can retransmit from first set
        send_packet(self, first_worker_port, self.pktW0S0x3)
        verify_packet(self, self.expected_pktW0S0x3, first_worker_port)


class NonSwitchML(TwoWorkerTest):
    """
    Test forwarding non-SwitchML traffic
    """

    def runTest(self):
        p = (Ether(dst=self.all_workers[1].mac, src=self.all_workers[0].mac) /
             IP(dst=self.all_workers[1].ip, src=self.all_workers[0].ip) /
             "012345678901234567890123456789")

        send_packet(self, 0, p)
        verify_packet(self, p, 1)

        send_packet(self, 1, p)
        verify_packet(self, p, 1)

        send_packet(self, 2, p)
        verify_packet(self, p, 1)

        q = (Ether(dst=self.all_workers[2].mac, src=self.all_workers[0].mac) /
             IP(dst=self.all_workers[2].ip, src=self.all_workers[0].ip) /
             "012345678901234567890123456789")

        send_packet(self, 0, q)
        verify_packet(self, q, 2)

        send_packet(self, 1, q)
        verify_packet(self, q, 2)

        send_packet(self, 2, q)
        verify_packet(self, q, 2)

class DifferentPortsReduction(TwoWorkerTest):
    """
    Test reductions leveraging port masks in the switch to do core steering.
    """

    def runTest(self):
        # do a straightforward reduction in the first set of slot 0
        send_packet(self, first_worker_port, self.pktW0S0)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S0)

        verify_packet(self, self.expected_pktW0S0, first_worker_port)
        verify_packet(self, self.expected_pktW1S0, second_worker_port)

        # do a straightforward reduction in the first set of slot 1 with different ports
        send_packet(self, first_worker_port, self.pktW0S0p1)
        verify_no_other_packets(self)

        send_packet(self, second_worker_port, self.pktW1S0p1)

        verify_packet(self, self.expected_pktW0S0p1, first_worker_port)
        verify_packet(self, self.expected_pktW1S0p1, second_worker_port)
        
        # self.pktW0S0p1.show()
        # self.pktW1S0p1.show()
        # self.expected_pktW0S0p1.show()
        # self.expected_pktW1S0p1.show()
        

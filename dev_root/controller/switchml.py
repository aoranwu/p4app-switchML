#  Copyright 2021 Intel-KAUST-Microsoft
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys
import glob
import yaml
import signal
import asyncio
import argparse
import logging
from concurrent import futures

# Add BF Python to search path
bfrt_location = '{}/lib/python*/site-packages/tofino'.format(
    os.environ['SDE_INSTALL'])
sys.path.append(glob.glob(bfrt_location)[0])
import bfrt_grpc.client as gc

from forwarder import Forwarder
from ports import Ports
from pre import PRE
from arp_icmp_responder import ARPandICMPResponder
from drop_simulator import DropSimulator
from rdma_receiver import RDMAReceiver
from udp_receiver import UDPReceiver
from bitmap_checker import BitmapChecker
from workers_counter import WorkersCounter
from exponents import Exponents
from processor import Processor
from next_step_selector import NextStepSelector
from rdma_sender import RDMASender
from udp_sender import UDPSender
from set_switch_type import SetSwitchType
from set_mgid_offset_factor import SetMgidOffsetFactor
from get_port_from_worker_id import GetPortFromWorkerID
from grpc_server import GRPCServer
from cli import Cli
from common import front_panel_regex, mac_address_regex, validate_ip

class SwitchML(object):
    '''SwitchML controller'''

    def __init__(self):
        super(SwitchML, self).__init__()

        self.log = logging.getLogger(__name__)
        self.log.info('SwitchML controller')

        # CPU PCIe port
        self.cpu_port = 320  # Pipe 2 Quad 16

        # UDP port and mask
        self.udp_port = 0xbee0
        self.udp_mask = 0xfff0

        # RDMA partition key
        self.switch_pkey = 0xffff

        # Set all nodes MGID
        self.all_ports_mgid = 0x8000
        self.all_ports_initial_rid = 0x8000

        # Multicast group ID -> replication ID (= node ID) -> port
        self.multicast_groups = {self.all_ports_mgid: {}}

        self.switch_macs = ["06:00:00:00:00:02","06:00:00:00:00:03","06:00:00:00:00:01"]
        self.switch_ips = ["198.19.200.202","198.19.200.203","198.19.200.201"] 

    def critical_error(self, msg):
        self.log.critical(msg)
        print(msg, file=sys.stderr)
        logging.shutdown()
        #sys.exit(1)
        os.kill(os.getpid(), signal.SIGTERM)

    def setup(
        self,
        program,
        switch_mac,
        switch_ip,
        bfrt_ip,
        bfrt_port,
        ports_file,
        use_multipipe,
        use_model
    ):
        self.use_multipipe = use_multipipe
        self.use_model = use_model
        # Device 0
        self.dev = 0
        # Target all pipes
        self.target = gc.Target(self.dev, pipe_id=0xFFFF)
        # Connect to BFRT server
        try:
            interface = gc.ClientInterface('{}:{}'.format(bfrt_ip, bfrt_port),
                                           client_id=0,
                                           device_id=self.dev)
                                           #is_master=True)
        except RuntimeError as re:
            msg = re.args[0] % re.args[1]
            self.critical_error(msg)
        else:
            self.log.info('Connected to BFRT server {}:{}'.format(
                bfrt_ip, bfrt_port))

        try:
            interface.bind_pipeline_config(program)
        except gc.BfruntimeForwardingRpcException:
            self.critical_error('P4 program {} not found!'.format(program))

        try:
            # Get all tables for program
            self.bfrt_info = interface.bfrt_info_get(program)

            # Ports table
            self.ports = Ports(self.target, gc, self.bfrt_info)

            # Enable loopback on front panel ports
            loopback_ports = (
                [64] +  # Pipe 0 CPU ethernet port
                # Pipe 0: all 16 front-panel ports
                #list(range(  0,  0+64,4)) +
                # Pipe 1: all 16 front-panel ports
                list(range(128, 128 + 64, 4)) +
                # Pipe 2: all 16 front-panel ports
                list(range(256, 256 + 64, 4)) +
                # Pipe 3: all 16 front-panel ports
                list(range(384, 384 + 64, 4)))
            print('Setting {} front panel ports in loopback mode'.format(
                len(loopback_ports)))
            self.ports.set_loopback_mode(loopback_ports)

            # Enable loopback on PktGen ports
            pktgen_ports = [192, 448]
            if not self.use_model:
                print('\nYou must \'remove\' the ports in the BF ucli:\n')
                for p in pktgen_ports:
                    print('    bf-sde> dvm rmv_port 0 {}'.format(p))
                input('\nPress Enter to continue...')

                if not self.ports.set_loopback_mode_pktgen(pktgen_ports):
                    self.critical_error(
                        'Failed setting front panel ports in loopback mode')

                print('\nAdd the ports again:\n')
                for p in pktgen_ports:
                    print('    bf-sde> dvm add_port 0 {} 100 0'.format(p))
                input('\nPress Enter to continue...')

            # Packet Replication Engine table
            self.pre = PRE(self.target, gc, self.bfrt_info, self.cpu_port)

            # Setup tables
            # Forwarder
            self.forwarder = Forwarder(self.target, gc, self.bfrt_info,
                                       self.all_ports_mgid)
            # ARP and ICMP responder
            self.arp_and_icmp = ARPandICMPResponder(self.target, gc,
                                                    self.bfrt_info)
            # Drop simulator
            self.drop_simulator = DropSimulator(self.target, gc, self.bfrt_info)
            # RDMA receiver
            self.rdma_receiver = RDMAReceiver(self.target, gc, self.bfrt_info)
            # UDP receiver
            self.udp_receiver = UDPReceiver(self.target, gc, self.bfrt_info)
            # Bitmap checker
            self.bitmap_checker = BitmapChecker(self.target, gc, self.bfrt_info)
            # Workers counter
            self.workers_counter = WorkersCounter(self.target, gc,
                                                  self.bfrt_info)
            # Worker id and port mapping
            self.get_port_from_worker_id = GetPortFromWorkerID(gc, self.bfrt_info)
            # Exponents
            self.exponents = Exponents(self.target, gc, self.bfrt_info)
            # Processors
            self.processors = []
            for i in range(32):
                p = Processor(self.target, gc, self.bfrt_info, i)
                self.processors.append(p)
            # Next step selector
            self.next_step_selector = NextStepSelector(self.target, gc,
                                                       self.bfrt_info,self.use_multipipe, self.use_model)
            # RDMA sender
            self.rdma_sender = RDMASender(self.target, gc, self.bfrt_info)
            # UDP sender
            self.udp_sender = UDPSender(self.target, gc, self.bfrt_info)

            self.set_switch_type = SetSwitchType(gc, self.bfrt_info)
            self.set_mgid_offset_factor = SetMgidOffsetFactor(gc, self.bfrt_info)

            # Add multicast group for flood
            self.pre.add_multicast_group(self.all_ports_mgid)

            # Enable ports
            success, ports = self.load_ports_file(ports_file)
            if not success:
                self.critical_error(ports)

            # Set switch addresses
            self.set_switch_mac_and_ip(switch_mac, switch_ip, self.use_multipipe)

            # CLI setup
            self.cli = Cli()
            self.cli.setup(self, prompt='SwitchML', name='SwitchML controller')

            # Set up gRPC server
            self.grpc_server = GRPCServer(ip='[::]', port=50099)

            # Run event loop for gRPC server in a separate thread
            # limit concurrency to 1 to avoid synchronization problems in the BFRT interface
            self.grpc_executor = futures.ThreadPoolExecutor(max_workers=1)

            self.event_loop = asyncio.get_event_loop()

        except KeyboardInterrupt:
            self.critical_error('Stopping controller.')
        except Exception as e:
            self.log.exception(e)
            self.critical_error('Unexpected error. Stopping controller.')

    def load_ports_file(self, ports_file):
        ''' Load ports yaml file and enable front panel ports.

            Keyword arguments:
                ports_file -- yaml file name

            Returns:
                (success flag, list of ports or error message)
        '''

        ports = []
        fib = {}

        with open(ports_file) as f:
            yaml_ports = yaml.safe_load(f)

            for port, value in yaml_ports['ports'].items():

                re_match = front_panel_regex.match(port)
                if not re_match:
                    return (False, 'Invalid port {}'.format(port))

                fp_port = int(re_match.group(1))
                fp_lane = int(re_match.group(2))

                # Convert all keys to lowercase
                value = {k.lower(): v for k, v in value.items()}

                if 'speed' in value:
                    try:
                        speed = int(value['speed'].upper().replace('G',
                                                                   '').strip())
                    except ValueError:
                        return (False, 'Invalid speed for port {}'.format(port))

                    if speed not in [10, 25, 40, 50, 100]:
                        return (
                            False,
                            'Port {} speed must be one of 10G,25G,40G,50G,100G'.
                            format(port))
                else:
                    speed = 100

                if 'fec' in value:
                    fec = value['fec'].lower().strip()
                    if fec not in ['none', 'fc', 'rs']:
                        return (False,
                                'Port {} fec must be one of none, fc, rs'.
                                format(port))
                else:
                    fec = 'none'

                if 'autoneg' in value:
                    an = value['autoneg'].lower().strip()
                    if an not in ['default', 'enable', 'disable']:
                        return (
                            False,
                            'Port {} autoneg must be one of default, enable, disable'
                            .format(port))
                else:
                    an = 'default'

                if 'mac' not in value:
                    return (False,
                            'Missing MAC address for port {}'.format(port))

                success, dev_port = self.ports.get_dev_port(fp_port, fp_lane)
                if success:
                    fib[dev_port] = value['mac'].upper()
                else:
                    return (False, dev_port)

                ports.append((fp_port, fp_lane, speed, fec, an))

        # Add ports
        success, error_msg = self.ports.add_ports(ports)
        if not success:
            return (False, error_msg)

        # Add forwarding entries
        self.forwarder.add_entries(fib.items())

        # Add ports to flood multicast group
        rids_and_ports = [
            (self.all_ports_initial_rid + dp, dp) for dp in fib.keys()
        ]
        success, error_msg = self.pre.add_multicast_nodes(
            self.all_ports_mgid, rids_and_ports)
        if not success:
            return (False, error_msg)

        for r, p in rids_and_ports:
            self.multicast_groups[self.all_ports_mgid][r] = p

        return (True, ports)

    def set_switch_mac_and_ip(self, switch_mac, switch_ip, use_mps):
        ''' Set switch MAC and IP '''
        self.switch_mac = switch_mac.upper()
        self.switch_ip = switch_ip

        self.arp_and_icmp.set_switch_mac_and_ip(self.switch_mac, self.switch_ip)
        self.rdma_receiver.set_switch_mac_and_ip(self.switch_mac,
                                                 self.switch_ip)
        self.udp_receiver.set_switch_mac_and_ip(self.switch_mac, self.switch_ip)
        self.rdma_sender.set_switch_mac_and_ip(self.switch_mac, self.switch_ip)
        if not use_mps:
            self.udp_sender.set_switch_mac_and_ip(self.switch_mac, self.switch_ip)
        else:
            for i in range(3):
                self.udp_sender.set_switch_mac_and_ip_for_pipe(self.switch_macs[i], self.switch_ips[i], i)


    def get_switch_mac_and_ip(self):
        ''' Get switch MAC and IP '''
        return self.switch_mac, self.switch_ip

    def clear_multicast_group(self, session_id):
        ''' Remove multicast group and nodes for this session '''

        if session_id in self.multicast_groups:
            for node_id in self.multicast_groups[session_id]:
                self.pre.remove_multicast_node(node_id)
            self.pre.remove_multicast_group(session_id)

            del self.multicast_groups[session_id]

    def clear_rdma_workers(self, session_id):
        ''' Reset UDP workers state for this session '''
        #TODO selectively remove workers (RDMA or UDP) for
        #this session, clear RDMA sender/receiver counters,
        #clear bitmap/count/exponents/processors
        self.rdma_receiver._clear()
        self.rdma_sender.clear_rdma_workers()
        self.bitmap_checker._clear()
        self.workers_counter._clear()
        self.exponents._clear()
        for p in self.processors:
            p._clear()

        self.clear_multicast_group(session_id)

    def add_rdma_worker(self, session_id, worker_id, num_workers, worker_mac,
                        worker_ip, worker_rkey, packet_size, message_size,
                        qpns_and_psns):
        ''' Add SwitchML RDMA worker.

            Keyword arguments:
                session_id -- ID of the session
                worker_id -- worker rank
                num_workers -- number of workers in this session
                worker_mac -- worker MAC address
                worker_ip -- worker IP address
                worker_rkey -- worker remote key
                packet_size -- MTU for this session
                message_size -- RDMA message size for this session
                qpns_and_psns -- list of (QPn, initial psn) tuples

            Returns:
                (success flag, None or error message)
        '''
        if worker_id >= 32:
            error_msg = 'Worker ID {} too large; only 32 workers supported'.format(
                worker_id)
            self.log.error(error_msg)
            return (False, error_msg)

        if num_workers > 32:
            error_msg = 'Worker count {} too large; only 32 workers supported'.format(
                num_workers)
            self.log.error(error_msg)
            return (False, error_msg)

        # Get port for node
        success, dev_port = self.forwarder.get_dev_port(worker_mac)
        if not success:
            return (False, dev_port)

        # Multicast groups below 0x8000 are used for sessions
        # (the mgid is the session id)
        session_id = session_id % 0x8000

        # Add RDMA receiver/sender entries
        success, error_msg = self.rdma_receiver.add_rdma_worker(
            worker_id, worker_ip, self.switch_pkey, packet_size, num_workers,
            session_id)
        if not success:
            return (False, error_msg)

        self.rdma_sender.add_rdma_worker(worker_id, worker_mac, worker_ip,
                                         worker_rkey, packet_size, message_size,
                                         qpns_and_psns)

        # Add multicast group if not present
        if session_id not in self.multicast_groups:
            self.pre.add_multicast_group(session_id)
            self.multicast_groups[session_id] = {}

        if worker_id in self.multicast_groups[
                session_id] and self.multicast_groups[session_id][
                    worker_id] != dev_port:
            # Existing node with different port, remove it
            self.pre.remove_multicast_node(worker_id)
            del self.multicast_groups[session_id][worker_id]

        # Add multicast node if not present
        if worker_id not in self.multicast_groups[session_id]:
            # Add new node
            success, error_msg = self.pre.add_multicast_node(
                session_id, worker_id, dev_port)
            if not success:
                return (False, error_msg)

            self.multicast_groups[session_id][worker_id] = dev_port

        self.log.info('Added RDMA worker {}:{} {}'.format(
            worker_id, worker_mac, worker_ip))

        return (True, None)

    def clear_udp_workers(self, session_id):
        ''' Reset UDP workers state for this session '''
        #TODO selectively remove workers (RDMA or UDP) for
        #this session, clear UDP sender/receiver counters,
        #clear bitmap/count/exponents/processors
        self.udp_receiver._clear()
        self.udp_sender.clear_udp_workers()
        self.bitmap_checker._clear()
        self.workers_counter._clear()
        self.exponents._clear()
        for p in self.processors:
            p._clear()

        self.clear_multicast_group(session_id)

    def add_udp_worker(self, session_id, worker_id, num_workers, worker_mac,
                       worker_ip, udp_port=0xbee0):
        ''' Add SwitchML UDP worker.

            Keyword arguments:
                session_id -- ID of the session
                worker_id -- worker rank
                num_workers -- number of workers in this session
                worker_mac -- worker MAC address
                worker_ip -- worker IP address

            Returns:
                (success flag, None or error message)
        '''
        #TODO session packet size
        if worker_id >= 32:
            error_msg = 'Worker ID {} too large; only 32 workers supported'.format(
                worker_id)
            self.log.error(error_msg)
            return (False, error_msg)

        if num_workers > 32:
            error_msg = 'Worker count {} too large; only 32 workers supported'.format(
                num_workers)
            self.log.error(error_msg)
            return (False, error_msg)

        # Get port for node
        success, dev_port = self.forwarder.get_dev_port(worker_mac)
        if not success:
            return (False, dev_port)

        # Multicast groups below 0x8000 are used for sessions
        # (the mgid is the session id)
        session_id = session_id % 0x8000

        # Add UDP receiver/sender entries
        success, error_msg = self.udp_receiver.add_udp_worker(
            worker_id, worker_mac, worker_ip, self.udp_port, self.udp_mask,
            num_workers, session_id)
        if not success:
            return (False, error_msg)

        self.udp_sender.add_udp_worker(worker_id, worker_mac, worker_ip)
                # set udp port for the worker
        self.udp_sender.set_udp_port_for_worker(worker_id,udp_port)

        # add to worker_id egress port mapping
        self.get_port_from_worker_id.set_port_for_worker_id(worker_id, dev_port)

        # Add multicast group if not present
        if session_id not in self.multicast_groups:
            self.pre.add_multicast_group(session_id)
            self.multicast_groups[session_id] = {}

        if worker_id in self.multicast_groups[
                session_id] and self.multicast_groups[session_id][
                    worker_id] != dev_port:
            # Existing node with different port, remove it
            self.pre.remove_multicast_node(worker_id)
            del self.multicast_groups[session_id][worker_id]

        # Add multicast node if not present
        if worker_id not in self.multicast_groups[session_id]:
            # Add new node
            success, error_msg = self.pre.add_multicast_node(
                session_id, worker_id, dev_port)
            if not success:
                return (False, error_msg)

            self.multicast_groups[session_id][worker_id] = dev_port

        self.log.info('Added UDP worker {}:{} {}'.format(
            worker_id, worker_mac, worker_ip))

        return (True, None)

    def add_udp_worker_for_pipe(self, session_id, worker_id, num_workers, worker_mac,
                       worker_ip, udp_port, pipe):
        ''' Add SwitchML UDP worker.

            Keyword arguments:
                session_id -- ID of the session
                worker_id -- worker rank
                num_workers -- number of workers in this session
                worker_mac -- worker MAC address
                worker_ip -- worker IP address

            Returns:
                (success flag, None or error message)
        '''
        #TODO session packet size
        if worker_id >= 32:
            error_msg = 'Worker ID {} too large; only 32 workers supported'.format(
                worker_id)
            self.log.error(error_msg)
            return (False, error_msg)

        if num_workers > 32:
            error_msg = 'Worker count {} too large; only 32 workers supported'.format(
                num_workers)
            self.log.error(error_msg)
            return (False, error_msg)

        # Get port for node
        success, dev_port = self.forwarder.get_dev_port(worker_mac)
        if not success:
            return (False, dev_port)

        # Multicast groups below 0x8000 are used for sessions
        # (the mgid is the session id)
        session_id = session_id % 0x8000
        session_id += pipe

        # Add UDP receiver/sender entries
        success, error_msg = self.udp_receiver.add_udp_worker_for_pipe(
            worker_id, worker_mac, worker_ip, self.udp_port, self.udp_mask,
            num_workers, session_id, pipe)
        if not success:
            return (False, error_msg)

        self.udp_sender.add_udp_worker_for_pipe(worker_id, worker_mac, worker_ip, pipe)
        # set udp port for the worker
        self.udp_sender.set_udp_port_for_worker_for_pipe(worker_id,udp_port,pipe)

        # add to worker_id egress port mapping
        self.get_port_from_worker_id.set_port_for_worker_id_for_pipe(worker_id, dev_port, pipe)

        # Add multicast group if not present
        if session_id not in self.multicast_groups:
            self.pre.add_multicast_group(session_id)
            self.multicast_groups[session_id] = {}

        if worker_id in self.multicast_groups[
                session_id] and self.multicast_groups[session_id][
                    worker_id] != dev_port:
            # Existing node with different port, remove it
            self.pre.remove_multicast_node(worker_id)
            del self.multicast_groups[session_id][worker_id]

        # Add multicast node if not present
        if worker_id not in self.multicast_groups[session_id]:
            # Add new node
            success, error_msg = self.pre.add_multicast_node(
                session_id, worker_id, dev_port)
            if not success:
                return (False, error_msg)

            self.multicast_groups[session_id][worker_id] = dev_port

        self.log.info('Added UDP worker {}:{} {}'.format(
            worker_id, worker_mac, worker_ip))

        return (True, None)

    def run(self):
        try:
            # Start listening for RPCs
            self.grpc_future = self.grpc_executor.submit(
                self.grpc_server.run, self.event_loop, self)

            self.log.info('gRPC server started')

            # Start CLI
            self.cli.run()

            # Stop gRPC server and event loop
            self.event_loop.call_soon_threadsafe(self.grpc_server.stop)

            # Wait for gRPC thread to end
            self.grpc_future.result()

            # Stop event loop
            self.event_loop.close()

            # Close gRPC executor
            self.grpc_executor.shutdown()

            self.log.info('gRPC server stopped')

        except Exception as e:
            self.log.exception(e)

        self.log.info('Stopping controller')


if __name__ == '__main__':

    # Parse arguments
    argparser = argparse.ArgumentParser(description='SwitchML controller.')
    argparser.add_argument('--program',
                           type=str,
                           default='switchml',
                           help='P4 program name. Default: SwitchML')
    argparser.add_argument(
        '--bfrt-ip',
        type=str,
        default='127.0.0.1',
        help='Name/address of the BFRuntime server. Default: 127.0.0.1')
    argparser.add_argument('--bfrt-port',
                           type=int,
                           default=50052,
                           help='Port of the BFRuntime server. Default: 50052')
    argparser.add_argument(
        '--switch-mac',
        type=str,
        default='00:11:22:33:44:55',
        help='MAC address of the switch. Default: 00:11:22:33:44:55')
    argparser.add_argument('--switch-ip',
                           type=str,
                           default='10.0.0.254',
                           help='IP address of the switch. Default: 10.0.0.254')
    argparser.add_argument(
        '--ports',
        type=str,
        default='ports.yaml',
        help=
        'YAML file describing machines connected to ports. Default: ports.yaml')
    argparser.add_argument('--log-level',
                           default='INFO',
                           choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'],
                           help='Default: INFO')
    
    argparser.add_argument('--use-model',
                           default=False,
                           action='store_true',
                           help='Whether this program is run on tofino model or not')
    
    argparser.add_argument('--use-multipipe',
                           default=False,
                           action='store_true',
                           help='Whether this program uses multiple pipes to simulate multiple switches')

    args = argparser.parse_args()

    # Configure logging
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        sys.exit('Invalid log level: {}'.format(args.log_level))

    logformat = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename='switchml.log',
                        filemode='w',
                        level=numeric_level,
                        format=logformat,
                        datefmt='%H:%M:%S')

    args.switch_mac = args.switch_mac.strip().upper()
    args.switch_ip = args.switch_ip.strip()
    args.bfrt_ip = args.bfrt_ip.strip()

    if not mac_address_regex.match(args.switch_mac):
        sys.exit('Invalid Switch MAC address')
    if not validate_ip(args.switch_ip):
        sys.exit('Invalid Switch IP address')
    if not validate_ip(args.bfrt_ip):
        sys.exit('Invalid BFRuntime server IP address')

    ctrl = SwitchML()
    ctrl.setup(args.program, args.switch_mac, args.switch_ip, args.bfrt_ip,
               args.bfrt_port, args.ports, args.use_multipipe, args.use_model)

    # Start controller
    ctrl.run()

    # Flush log, stdout, stderr
    sys.stdout.flush()
    sys.stderr.flush()
    logging.shutdown()

    # Exit
    os.kill(os.getpid(), signal.SIGTERM)

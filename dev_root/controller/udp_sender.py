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

import logging
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
from control import Control


class UDPSender(Control):

    def __init__(self, target, gc, bfrt_info, ctrl=None):
        # Set up base class
        super(UDPSender, self).__init__(target, gc)

        self.log = logging.getLogger(__name__)

        self.tables = [
            bfrt_info.table_get('pipe.Egress.udp_sender.switch_mac_and_ip'),
            bfrt_info.table_get('pipe.Egress.udp_sender.dst_addr'),
            bfrt_info.table_get('pipe.Egress.udp_sender.set_dst_udp_port_tbl')
        ]
        self.ctrl = ctrl

        self.switch_mac_and_ip = self.tables[0]
        self.dst_addr = self.tables[1]
        self.set_dst_udp_port_tbl = self.tables[2]

        # Annotations
        self.switch_mac_and_ip.info.data_field_annotation_add(
            'switch_mac', 'Egress.udp_sender.set_switch_mac_and_ip', 'mac')
        self.switch_mac_and_ip.info.data_field_annotation_add(
            'switch_ip', 'Egress.udp_sender.set_switch_mac_and_ip', 'ipv4')
        self.dst_addr.info.data_field_annotation_add(
            'ip_dst_addr', 'Egress.udp_sender.set_dst_addr', 'ipv4')
        self.dst_addr.info.data_field_annotation_add(
            'eth_dst_addr', 'Egress.udp_sender.set_dst_addr', 'mac')

        # Clear tables and reset counters
        self._clear()

    def set_switch_mac_and_ip(self, switch_mac, switch_ip):
        ''' Set switch MAC and IP '''

        # Clear table
        self.switch_mac_and_ip.default_entry_reset(self.target)

        self.switch_mac_and_ip.default_entry_set(
            self.target,
            self.switch_mac_and_ip.make_data([
                self.gc.DataTuple('switch_mac', switch_mac),
                self.gc.DataTuple('switch_ip', switch_ip)
            ], 'Egress.udp_sender.set_switch_mac_and_ip'))
    
    def set_switch_mac_and_ip_for_pipe(self, switch_mac, switch_ip, pipe):
        ''' Set switch MAC and IP '''

        # # Clear table
        # self.switch_mac_and_ip.default_entry_reset(self.target)
        self.switch_mac_and_ip.attribute_entry_scope_set(self.target, predefined_pipe_scope=True,
                                                            predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
        self.switch_mac_and_ip.default_entry_set(
            self.targets[pipe],
            self.switch_mac_and_ip.make_data([
                self.gc.DataTuple('switch_mac', switch_mac),
                self.gc.DataTuple('switch_ip', switch_ip)
            ], 'Egress.udp_sender.set_switch_mac_and_ip'))

    def clear_udp_workers(self):
        ''' Remove all UDP workers '''
        self.dst_addr.entry_del(self.target)

    def reset_counters(self):
        ''' Reset sent UDP packets counters '''

        # Reset direct counter
        self.dst_addr.operations_execute(self.target, 'SyncCounters')
        resp = self.dst_addr.entry_get(self.target, flags={'from_hw': False})

        keys = []
        values = []

        for v, k in resp:
            keys.append(k)

            v = v.to_dict()
            k = k.to_dict()

            values.append(
                self.dst_addr.make_data([
                    self.gc.DataTuple('$COUNTER_SPEC_BYTES', 0),
                    self.gc.DataTuple('$COUNTER_SPEC_PKTS', 0)
                ], v['action_name']))

        self.dst_addr.entry_mod(self.target, keys, values)

    def add_udp_worker(self, worker_id, worker_mac, worker_ip):
        ''' Add SwitchML UDP entry.

            Keyword arguments:
                worker_id -- worker rank
                worker_mac -- worker MAC address
                worker_ip -- worker IP address
        '''
        self.dst_addr.entry_add(self.target, [
            self.dst_addr.make_key(
                [self.gc.KeyTuple('eg_md.switchml_md.worker_id', worker_id)])
        ], [
            self.dst_addr.make_data([
                self.gc.DataTuple('eth_dst_addr', worker_mac),
                self.gc.DataTuple('ip_dst_addr', worker_ip)
            ], 'Egress.udp_sender.set_dst_addr')
        ])
    
    def add_udp_worker_for_pipe(self, worker_id, worker_mac, worker_ip, pipe):
        ''' Add SwitchML UDP entry.

            Keyword arguments:
                worker_id -- worker rank
                worker_mac -- worker MAC address
                worker_ip -- worker IP address
        '''
        self.dst_addr.attribute_entry_scope_set(self.target, predefined_pipe_scope=True,
                                                            predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
        self.dst_addr.entry_add(self.targets[pipe], [
            self.dst_addr.make_key(
                [self.gc.KeyTuple('eg_md.switchml_md.worker_id', worker_id)])
        ], [
            self.dst_addr.make_data([
                self.gc.DataTuple('eth_dst_addr', worker_mac),
                self.gc.DataTuple('ip_dst_addr', worker_ip)
            ], 'Egress.udp_sender.set_dst_addr')
        ])
    
    # Set udp port for a worker with worker_id
    def set_udp_port_for_worker(self,worker_id,udp_port=0xbeef):
        # self.logger.info("Set udp port to be {} for worker with id {}".format(udp_port,worker_id))
        self.set_dst_udp_port_tbl.entry_add(
            self.target,
            [self.set_dst_udp_port_tbl.make_key([self.gc.KeyTuple('eg_md.switchml_md.worker_id',
                                              worker_id)])],
            [self.set_dst_udp_port_tbl.make_data([self.gc.DataTuple('dst_port', udp_port)],
                                  'Egress.udp_sender.set_dst_udp_port')])

    def set_udp_port_for_worker_for_pipe(self,worker_id,udp_port=0xbeef,pipe=0):
        # self.logger.info("Set udp port to be {} for worker with id {}".format(udp_port,worker_id))
        self.set_dst_udp_port_tbl.attribute_entry_scope_set(self.target, predefined_pipe_scope=True,
                                                            predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
        self.set_dst_udp_port_tbl.entry_add(
            self.targets[pipe],
            [self.set_dst_udp_port_tbl.make_key([self.gc.KeyTuple('eg_md.switchml_md.worker_id',
                                              worker_id)])],
            [self.set_dst_udp_port_tbl.make_data([self.gc.DataTuple('dst_port', udp_port)],
                                  'Egress.udp_sender.set_dst_udp_port')])

    def get_workers_counter(self, worker_id=None):
        ''' Get the current values of sent packets/bytes per UDP worker.
            If a worker ID is provided, it will return only the values for that
            worker, otherwise it will return all of them.
        '''


        
        if not self.ctrl.use_multipipe:
            self.dst_addr.operations_execute(self.target, 'SyncCounters')
            resp = self.dst_addr.entry_get(self.target, flags={'from_hw': False})
            pipe_num = 0xffff
            values = {}
            for v, k in resp:
                v = v.to_dict()
                k = k.to_dict()
                pipe = pipe_num
                id = k['eg_md.switchml_md.worker_id']['value']
                mac = v['eth_dst_addr']
                ip = v['ip_dst_addr']
                packets = v['$COUNTER_SPEC_PKTS']
                bytes = v['$COUNTER_SPEC_BYTES']

                if worker_id == None or worker_id == id:
                    values[id] = {
                        'Pipe': pipe,
                        'MAC': mac,
                        'IP': ip,
                        'spkts': packets,
                        'sbytes': bytes
                    }
        else:
            self.dst_addr.attribute_entry_scope_set(self.target, predefined_pipe_scope=True,
                                                            predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
            values = {}
            for pipe_num in range(4):
                self.dst_addr.operations_execute(self.targets[pipe_num], 'SyncCounters')
                resp = self.dst_addr.entry_get(self.targets[pipe_num], flags={'from_hw': False})
                for v, k in resp:
                    v = v.to_dict()
                    k = k.to_dict()
                    
                    pipe = pipe_num
                    id = k['eg_md.switchml_md.worker_id']['value']
                    mac = v['eth_dst_addr']
                    ip = v['ip_dst_addr']
                    packets = v['$COUNTER_SPEC_PKTS']
                    bytes = v['$COUNTER_SPEC_BYTES']
                    
                    if worker_id == None or worker_id == id:
                        values[id] = {
                            'Pipe': pipe,
                            'MAC': mac,
                            'IP': ip,
                            'spkts': packets,
                            'sbytes': bytes
                        }
        
        return values

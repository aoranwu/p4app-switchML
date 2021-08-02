import logging
from pprint import pprint, pformat
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import grpc

from Table import Table

class SetMgidOffsetFactor(Table):
    def __init__(self, client, bfrt_info):
        # set up base class
        super(SetMgidOffsetFactor, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('SetMgidOffsetFactor')
        self.logger.info("Setting up SetMgidOffsetFactor table...")

        # getting the table
        self.set_mgid_offset_factor = self.bfrt_info.table_get("pipe.Ingress.set_mgid_offset_factor.set_mgid_offset_factor_tbl")


    def set_default_entry(self, offset):
        # self.clear()
        self.set_mgid_offset_factor.default_entry_set(
                self.target,
                self.set_mgid_offset_factor.make_data([gc.DataTuple('offset_factor',offset)],'Ingress.set_mgid_offset_factor.set_mgid_offset_factor')
            )
    
    def set_default_entry_for_pipe(self, offset, pipe=0):
        # self.clear()
        self.set_mgid_offset_factor.attribute_entry_scope_set(self.target, predefined_pipe_scope=True,
                                                            predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
        self.set_mgid_offset_factor.default_entry_set(
                self.targets[pipe],
                self.set_mgid_offset_factor.make_data([gc.DataTuple('offset_factor',offset)],'Ingress.set_mgid_offset_factor.set_mgid_offset_factor')
            )

    
    def clear(self):
        self.set_mgid_offset_factor.entry_del(self.target)

        # if pipe==-1:
        #     if isinstance(self.target,List):
        #         self.target = gc.Target(device_id=0,pipe_id=0xffff)
        #     if is_root_switch:
        #         self.set_switch_type.default_entry_set(
        #             self.target,
        #             self.set_switch_type.make_data([],'Ingress.set_switch.set_root')
        #         )
        #     else:
        #         self.set_switch_type.default_entry_set(
        #             self.target,
        #             self.set_switch_type.make_data([],'Ingress.set_switch.set_non_root')
        #         )
        # else:
        #     # TODO: test if device has 4 pipes, and parameter pipe is valid
        #     target = gc.Target(device_id=0,pipe_id=0xffff)
        #     self.set_switch_type.attribute_entry_scope_set(target, predefined_pipe_scope=True,
        #                                                     predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
        #     self.target = []
        #     for i in range(4):
        #         self.target.append(gc.Target(device_id=0,pipe_id=i))

        #     if is_root_switch:
        #         self.set_switch_type.default_entry_set(
        #             self.target[pipe],
        #             self.set_switch_type.make_data([],'Ingress.set_switch.set_root')
        #         )
        #     else:
        #         self.set_switch_type.default_entry_set(
        #             self.target[pipe],
        #             self.set_switch_type.make_data([],'Ingress.set_switch.set_non_root')
        #         )
import logging
from pprint import pprint, pformat
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import grpc

from Table import Table

class SetUseHierAggre(Table):
    def __init__(self, client, bfrt_info):
        # set up base class
        super(SetUseHierAggre, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('SetUseHierAggre')
        self.logger.info("Setting up set_use_hier_aggre_tbl table...")

        # getting the table
        self.set_use_hier_aggre_tbl = self.bfrt_info.table_get("pipe.Egress.set_use_hier_aggre.set_use_hier_aggre_tbl")


    def set_default_entry(self, use_hier_aggre):
        # self.clear()
        self.set_use_hier_aggre_tbl.default_entry_set(
                self.target,
                self.set_use_hier_aggre_tbl.make_data([gc.DataTuple('use_hier_aggre',use_hier_aggre)],'Egress.set_use_hier_aggre.set_use_hier_aggre')
            )
    
    def set_default_entry_for_pipe(self, use_hier_aggre, pipe=0):
        # self.clear()
        self.set_use_hier_aggre_tbl.attribute_entry_scope_set(self.target, predefined_pipe_scope=True,
                                                            predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
        self.set_use_hier_aggre_tbl.default_entry_set(
                self.targets[pipe],
                self.set_use_hier_aggre_tbl.make_data([gc.DataTuple('use_hier_aggre',use_hier_aggre)],'Egress.set_use_hier_aggre.set_use_hier_aggre')
            )

    
    def clear(self):
        self.set_switch_type.entry_del(self.target)

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

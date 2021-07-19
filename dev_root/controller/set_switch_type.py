import logging
from pprint import pprint, pformat
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import grpc

from Table import Table

class SetSwitchType(Table):
    def __init__(self, client, bfrt_info):
        # set up base class
        super(SetSwitchType, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('SetSwitchType')
        self.logger.info("Setting up set_switch_type table...")

        # getting the table
        self.set_switch_type = self.bfrt_info.table_get("pipe.Ingress.set_switch.set_switch_type")

        # set the switch to be non-root by default
        self.set_default_entry(False)

    def set_default_entry(self, is_root_switch):
        self.clear()
        if is_root_switch:
            self.set_switch_type.default_entry_set(
                self.target,
                self.set_switch_type.make_data([],'Ingress.set_switch.set_root')
            )
        else:
            self.set_switch_type.default_entry_set(
                self.target,
                self.set_switch_type.make_data([],'Ingress.set_switch.set_non_root')
            )

    def clear(self):
        self.set_switch_type.entry_del(self.target)
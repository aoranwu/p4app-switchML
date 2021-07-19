import logging
from pprint import pprint, pformat
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import grpc

from Table import Table

class SetUpwardPort(Table):
    def __init__(self, client, bfrt_info):
        # set up base class
        super(SetUpwardPort, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('SetUpwardPort')
        self.logger.info("Setting up set_upward_port_tbl table...")

        # getting the table
        self.set_upward_port_tbl = self.bfrt_info.table_get("pipe.Ingress.set_upward_port.set_upward_port_tbl")


    def set_default_entry(self, upward_port):
        self.clear()
        self.set_upward_port_tbl.default_entry_set(
            self.target,
            self.set_upward_port_tbl.make_data([gc.DataTuple('upward_port',upward_port)],'Ingress.set_upward_port.set_upward_port')
        )



    def clear(self):
        self.set_upward_port_tbl.entry_del(self.target)
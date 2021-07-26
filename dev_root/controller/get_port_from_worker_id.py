import logging
from pprint import pprint, pformat
import bfrt_grpc.bfruntime_pb2 as bfruntime_pb2
import bfrt_grpc.client as gc
import grpc

from Table import Table

class GetPortFromWorkerID(Table):
    def __init__(self, client, bfrt_info):
        # set up base class
        super(GetPortFromWorkerID, self).__init__(client, bfrt_info)

        self.logger = logging.getLogger('GetPortFromWorkerID')
        self.logger.info("Setting up get_port_from_worker_id table...")

        # getting the table
        self.get_port_from_worker_id = self.bfrt_info.table_get("pipe.Ingress.get_port_from_worker_id.get_port_from_worker_id")
        self.clear()

    def set_port_for_worker_id(self, worker_id, port):
        
        self.get_port_from_worker_id.entry_add(
            self.target,
            [self.get_port_from_worker_id.make_key([gc.KeyTuple('ig_md.switchml_md.original_worker_id',
                                                                    worker_id)])],
            [self.get_port_from_worker_id.make_data([gc.DataTuple('port',port)],
                                                        'Ingress.get_port_from_worker_id.set_egress_port')]

        )

    def set_port_for_worker_id_for_pipe(self, worker_id, port, pipe):
        self.get_port_from_worker_id.attribute_entry_scope_set(self.target, predefined_pipe_scope=True,
                                                            predefined_pipe_scope_val=bfruntime_pb2.Mode.SINGLE)
        self.get_port_from_worker_id.entry_add(
            self.targets[pipe],
            [self.get_port_from_worker_id.make_key([gc.KeyTuple('ig_md.switchml_md.original_worker_id',
                                                                    worker_id)])],
            [self.get_port_from_worker_id.make_data([gc.DataTuple('port',port)],
                                                        'Ingress.get_port_from_worker_id.set_egress_port')]

        )


    def clear(self):
        self.get_port_from_worker_id.entry_del(self.target)
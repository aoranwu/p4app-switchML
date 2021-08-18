#ifndef _GET_PORT_FROM_WORKER_ID_
#define _GET_PORT_FROM_WORKER_ID_

#include "types.p4"
#include "headers.p4"

// Set switch type to be root or non-root
control GetPortFromWorkerID(in ingress_metadata_t ig_md, inout ingress_intrinsic_metadata_for_tm_t ig_tm_md){

    action set_egress_port(PortId_t port){
        // ig_md.switchml_md.is_root_switch = 0;
        ig_tm_md.ucast_egress_port = port;
    }

    table get_port_from_worker_id{
        key = {
            // match on the lower 16 bits
            ig_md.switchml_md.original_worker_id : ternary; // who are we sending to?
        }
        actions = {
            set_egress_port();
        }
        // need to change default action in control plane for root switch
        default_action = set_egress_port(64);
    }
    apply {
        get_port_from_worker_id.apply();
    }

}


#endif /* GET_PORT_FROM_WORKER_ID */
#ifndef _SET_UPWARD_PORT_
#define _SET_UPWARD_PORT_

#include "types.p4"
#include "headers.p4"

// Set switch type to be root or non-root
control SetUpwardPort(inout switchml_md_h switchml_md){
    action set_upward_port(PortId_t upward_port){
        switchml_md.upward_port = upward_port;
    }

    table set_upward_port_tbl{
        actions = {
            set_upward_port;
        }
        default_action = set_upward_port(0);
    }
    apply {
        set_upward_port_tbl.apply();
    }

}


#endif /* _SET_UPWARD_PORT_ */
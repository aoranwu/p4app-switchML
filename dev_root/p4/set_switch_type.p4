#ifndef _SET_SWITCH_TYPE_
#define _SET_SWITCH_TYPE_

#include "types.p4"
#include "headers.p4"

// Set switch type to be root or non-root
control SetSwitchType(inout switchml_md_h switchml_md){
    // action set_root(){
    //     // ig_md.switchml_md.is_root_switch = 1;
    //     switchml_md.is_root_switch = 1;
    // }

    // action set_non_root(){
    action set_root(bit<1> is_root,PortId_t upward_port){
        // ig_md.switchml_md.is_root_switch = 0;
        switchml_md.is_root_switch = is_root;
        switchml_md.upward_port = upward_port;
    }

    table set_switch_type{
        actions = {
            set_root;
        }
        // need to change default action in control plane for root switch
        default_action = set_root(0,0);
    }
    apply {
        set_switch_type.apply();
    }

}


#endif /* _SET_SWITCH_TYPE_ */
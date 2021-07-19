#ifndef _SET_SWITCH_TYPE_
#define _SET_SWITCH_TYPE_

#include "types.p4"
#include "headers.p4"

// Set switch type to be root or non-root
control SetSwitchType(inout switchml_md_h switchml_md){
    action set_root(){
        // ig_md.switchml_md.is_root_switch = 1;
        switchml_md.is_root_switch = 1;
    }

    action set_non_root(){
        // ig_md.switchml_md.is_root_switch = 0;
        switchml_md.is_root_switch = 0;
    }

    table set_switch_type{
        actions = {
            set_root;
            set_non_root;
        }
        // need to change default action in control plane for root switch
        default_action = set_non_root();
    }
    apply {
        set_switch_type.apply();
    }

}


#endif /* _SET_SWITCH_TYPE_ */
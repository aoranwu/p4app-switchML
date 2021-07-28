#ifndef _SET_MGID_OFFSET_FACTOR_
#define _SET_MGID_OFFSET_FACTOR_

#include "types.p4"
#include "headers.p4"

// Set switch type to be root or non-root
control SetMgidOffsetFactor(inout ingress_metadata_t ig_md){
    
    action set_mgid_offset_factor(bit<16> offset_factor){
        // ig_md.switchml_md.is_root_switch = 0;
        ig_md.mgid_offset_factor = offset_factor;
    }

    table set_mgid_offset_factor_tbl{
        actions = {
            set_mgid_offset_factor;
        }
        // need to change default action in control plane for root switch
        default_action = set_mgid_offset_factor(0);
    }
    apply {
        set_mgid_offset_factor_tbl.apply();
    }

}


#endif /* _SET_SWITCH_TYPE_ */
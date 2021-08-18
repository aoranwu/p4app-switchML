#ifndef _SET_USE_HIER_AGGRE_
#define _SET_USE_HIER_AGGRE_

#include "types.p4"
#include "headers.p4"

// Set switch type to be root or non-root
control SetUseHierAggre(inout egress_metadata_t eg_md){
    

    // action set_non_root(){
    action set_use_hier_aggre(bit<8> use_hier_aggre){
        eg_md.use_hier_aggre  = use_hier_aggre;
    }

    table set_use_hier_aggre_tbl{
        actions = {
            set_use_hier_aggre;
        }
        // need to change default action in control plane for root switch
        default_action = set_use_hier_aggre(0);
    }
    apply {
        set_use_hier_aggre_tbl.apply();
    }

}


#endif /* _SET_USE_HIER_AGGRE_ */
cd $SDE
$ns sw1 ./run_p4_tests.sh -p switchml -f /home/aoranwu/p4app-switchML/dev_root/tests/port-json-files/ports_hybrid_ptf.json --no-veth -t /home/aoranwu/p4app-switchML/dev_root/tests/ptf-tests -s TwoWorkerTests_p2_hybrid.BasicReduction

cd $SDE
$ns sw3 ./run_p4_tests.sh -p switchml -f /home/aoranwu/ports_sw3_ptf.json --no-veth -t /home/aoranwu/p4app-switchML/dev_root/tests/ptf-tests -s TwoWorkerTests_sw3.BasicReduction

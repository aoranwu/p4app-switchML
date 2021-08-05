cd /home/aoranwu/p4app-switchML/dev_root/controller/
ip netns exec sw1 python switchml.py --switch-mac=06:00:00:00:00:01 --switch-ip=198.19.200.201 --ports=/home/aoranwu/p4app-switchML/dev_root/controller/ports1.yaml --use-model --switch-name=sw1 --switch-conf-file=/home/aoranwu/p4app-switchML/dev_root/controller/switch_conf.yaml --bfrt-ip=192.168.1.2 --bfrt-port=50052

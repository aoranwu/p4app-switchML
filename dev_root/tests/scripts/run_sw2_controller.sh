cd /home/aoranwu/p4app-switchML/dev_root/controller/
ip netns exec sw2 python switchml.py --switch-mac=06:00:00:00:00:02 --switch-ip=198.19.200.202 --ports=/home/aoranwu/p4app-switchML/dev_root/controller/ports2.yaml --use-model --switch-name=sw2 --switch-conf-file=/home/aoranwu/p4app-switchML/dev_root/controller/switch_conf.yaml

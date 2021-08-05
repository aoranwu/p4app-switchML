unset all_proxy
unset http_proxy
unset https_proxy
unset ftp_proxy
unset socks_proxy
unset no_proxy
unset ALL_PROXY
unset HTTP_PROXY
unset HTTPS_PROXY
unset FTP_PROXY
unset SOCKS_PROXY
unset NO_PROXY

cd /home/aoranwu/p4app-switchML/dev_root/controller/
ip netns exec sw1 python switchml.py --switch-mac=06:00:00:00:00:01 --switch-ip=198.19.200.201 --ports=/home/aoranwu/p4app-switchML/dev_root/controller/ports1.yaml --use-model --switch-name=sw1 --switch-conf-file=/home/aoranwu/p4app-switchML/dev_root/controller/switch_conf.yaml

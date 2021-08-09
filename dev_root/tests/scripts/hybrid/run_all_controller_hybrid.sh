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
python switchml_wrapper.py --switch-conf-meta=/home/aoranwu/p4app-switchML/dev_root/controller/switch_conf_meta_hybrid.yaml

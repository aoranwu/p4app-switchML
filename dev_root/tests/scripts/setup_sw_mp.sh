set_mgid_offset_factor_for_pipe 0 0
set_mgid_offset_factor_for_pipe 1 1
set_mgid_offset_factor_for_pipe 2 2

set_root_switch_for_pipe 2
worker_add_udp_for_pipe 0 2 06:00:00:00:00:02 198.19.200.202 48864 2
worker_add_udp_for_pipe 1 2 06:00:00:00:00:03 198.19.200.203 48864 2

set_non_root_switch_for_pipe 60 06:00:00:00:00:01 198.19.200.201 48864 0
worker_add_udp_for_pipe 2 2 de:08:be:d7:01:47 198.19.200.50 12345 0
worker_add_udp_for_pipe 3 2 62:68:1b:cb:18:05 198.19.200.49 12345 0

set_non_root_switch_for_pipe 188  06:00:00:00:00:01 198.19.200.201 48864 1
worker_add_udp_for_pipe 4 2 86:bd:7b:5c:b9:2b 198.19.200.48 12345 1
worker_add_udp_for_pipe 5 2 7e:0a:ae:fb:53:df 198.19.200.47 12345 1
exit

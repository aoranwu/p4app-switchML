ip link set veth0 netns sw1
ip link set veth2 netns sw1

ip link set veth1 netns sw2
ip link set veth4 netns sw2
ip link set veth5 netns sw2
ip link set veth6 netns sw2
ip link set veth7 netns sw2
ip link set veth8 netns sw2
ip link set veth9 netns sw2
ip link set veth10 netns sw2
ip link set veth11 netns sw2

ip link set veth3 netns sw3
ip link set veth12 netns sw3
ip link set veth13 netns sw3
ip link set veth14 netns sw3
ip link set veth15 netns sw3
ip link set veth16 netns sw3
ip link set veth17 netns sw3
ip link set veth18 netns sw3
ip link set veth19 netns sw3

ip netns exec sw1 ip link set lo up
ip netns exec sw1 ip link set veth0 up
ip netns exec sw1 ip link set veth2 up

ip netns exec sw2 ip link set lo up
ip netns exec sw2 ip link set veth1 up
ip netns exec sw2 ip link set veth4 up
ip netns exec sw2 ip link set veth5 up
ip netns exec sw2 ip link set veth6 up
ip netns exec sw2 ip link set veth7 up
ip netns exec sw2 ip link set veth8 up
ip netns exec sw2 ip link set veth9 up
ip netns exec sw2 ip link set veth10 up
ip netns exec sw2 ip link set veth11 up

ip netns exec sw3 ip link set lo up
ip netns exec sw3 ip link set veth3 up
ip netns exec sw3 ip link set veth12 up
ip netns exec sw3 ip link set veth13 up
ip netns exec sw3 ip link set veth14 up
ip netns exec sw3 ip link set veth15 up
ip netns exec sw3 ip link set veth16 up
ip netns exec sw3 ip link set veth17 up
ip netns exec sw3 ip link set veth18 up
ip netns exec sw3 ip link set veth19 up


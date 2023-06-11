sudo apt update

sudo apt install python3-venv python3-pip 

# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow etcd
sudo iptables -A INPUT -p tcp --dport 2379:2380 -j ACCEPT

# Allow apiserver
sudo iptables -A INPUT -p tcp --dport 6443 -j ACCEPT

# Allow Calico
sudo iptables -A INPUT -p tcp --dport 9099:9100 -j ACCEPT

# Allow BGP
sudo iptables -A INPUT -p tcp --dport 179 -j ACCEPT

# Allow NodePort
sudo iptables -A INPUT -p tcp --dport 30000:32767 -j ACCEPT

# Allow master
sudo iptables -A INPUT -p tcp --dport 10250:10258 -j ACCEPT

# Allow DNS (TCP and UDP)
sudo iptables -A INPUT -p tcp --dport 53 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 53 -j ACCEPT

# Allow local-registry
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# Allow local-apt
sudo iptables -A INPUT -p tcp --dport 5080 -j ACCEPT

# Allow RPCBind (if NFS is used)
sudo iptables -A INPUT -p tcp --dport 111 -j ACCEPT

# Allow IPIP protocol for Calico
sudo iptables -A INPUT -p ipencap -j ACCEPT

# Allow metrics-server
sudo iptables -A INPUT -p tcp --dport 8443 -j ACCEPT


sudo apt install curl openssl tar -y


sudo apt install socat conntrack ebtables ipset -y



#docker run -d -p 5000:5000 --name local-registry registry
#docker build -t localhost:5000/yolov3:v1 ./ml_model/yolo/api/ 





2023/06/08 08:51:33 Request 1: 1307 ms
2023/06/08 08:51:33 Request 2: 1796 ms
2023/06/08 08:51:36 Request 3: 2397 ms
2023/06/08 08:51:41 Request 4: 1122 ms
2023/06/08 08:51:43 Request 5: 716 ms
2023/06/08 08:51:44 Request 6: 1748 ms
2023/06/08 08:51:44 Request 7: 928 ms
2023/06/08 08:51:44 Request 8: 3119 ms
2023/06/08 08:51:46 Request 9: 1844 ms
2023/06/08 08:51:46 Request 10: 978 ms
2023/06/08 08:51:48 Request 11: 1533 ms
2023/06/08 08:51:50 Request 12: 2024 ms
2023/06/08 08:51:51 Request 13: 3335 ms
2023/06/08 08:51:52 Request 14: 2625 ms
2023/06/08 08:51:53 Request 15: 1532 ms
2023/06/08 08:51:54 Request 16: 1228 ms
2023/06/08 08:51:54 Request 17: 945 ms
2023/06/08 08:51:56 Request 18: 553 ms
2023/06/08 08:51:56 Request 19: 1942 ms
2023/06/08 08:51:58 Request 20: 1430 ms
2023/06/08 08:51:58 Request 21: 713 ms
2023/06/08 08:51:58 Request 3090: 713 ms


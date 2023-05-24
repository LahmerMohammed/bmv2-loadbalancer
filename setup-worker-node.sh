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
#docker build -t lovalhost:5000/yolo-v3:v1 ./ml_model/yolo/api/ 
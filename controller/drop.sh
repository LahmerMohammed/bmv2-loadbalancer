#!/bin/bash

sudo iptables -L | grep "DROP" | grep "tcp" | while read -r rule; do
    port=$(echo "$rule" | awk -F" " '{print $NF}' | awk -F":" '{print $2}')
        sudo iptables -D INPUT -p tcp --dport ${port} -j DROP
        echo ${port}
done

sudo iptables -A INPUT -p tcp --dport 8000 -j DROP

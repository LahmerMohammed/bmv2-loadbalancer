
from config import *
from helpers import *

from p4runtime_lib.switch import ShutdownAllSwitchConnections
from p4runtime_lib import bmv2, helper
from protobuf_to_dict import protobuf_to_dict
import grpc
from scapy.all import *

from loadbalancer import RoundRobin
import time
import subprocess


import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
        except OSError:
            return True
        return False

def add_iptables_rule(port):
    command = f"iptables -A INPUT -p tcp --dport {port} -j DROP"
    subprocess.run(command, shell=True, check=True)

def delete_iptables_rule(port):
    command = f"iptables -D INPUT -p tcp --dport {port} -j DROP"
    subprocess.run(command, shell=True, check=True)

class Controller:
    def __init__(self, p4i_file_path=BMV2_SWITCH['p4i_file_path'], bmv2_json_file_path=BMV2_SWITCH['json_file_path']) -> None:

        self.load_balancer = RoundRobin()
        self.port_map = {}
        self.p4i_helper = helper.P4InfoHelper(p4i_file_path)
        self.available_ports = list(range(10000, 65536))


        try:
            self.bmv2_sw = bmv2.Bmv2SwitchConnection(
                address=BMV2_SWITCH['server_addr'],
                device_id=BMV2_SWITCH['id'],
                proto_dump_file=BMV2_SWITCH['proto_dump_file'],
            )

            self.bmv2_sw.MasterArbitrationUpdate()

            self.bmv2_sw.SetForwardingPipelineConfig(p4info=self.p4i_helper.p4info,
                                                     bmv2_json_file_path=bmv2_json_file_path)

            print(
                "[✅] Installed loadbalancer P4 Program using SetForwardingPipelineConfig on the switch.")

        except grpc.RpcError as e:
            printGrpcError(e)


    def add_default_entries(self):
        self.add_send_frame_table_entry(port=BMV2_SWITCH["users_interface"]["switch_port"],
                                        mac_addr=BMV2_SWITCH["users_interface"]["mac"])

        for c_if in BMV2_SWITCH["cluster_interfaces"]:
            self.add_send_frame_table_entry(port=c_if["switch_port"],mac_addr=c_if["mac"])

        services = get_services()
        #Added services entries
        for key, _ in services.items():
            print(key)
            self.add_service_table_entry(port=key)

        print('[✅] Default entries added successfully ')


    def add_send_frame_table_entry(self, port: int, mac_addr: str):
        table_entry = self.p4i_helper.buildTableEntry(
            table_name='MyEgress.send_frame',
            match_fields={
                'standard_metadata.egress_spec': port
            },
            action_name='MyEgress.rewrite_mac',
            action_params={
                'smac': mac_addr
            }
        )
    
        self.bmv2_sw.WriteTableEntry(table_entry=table_entry)


    def add_snat_table_entry(self, entry: dict):
        table_entry = self.p4i_helper.buildTableEntry(
            table_name='MyIngress.snat_t',
            match_fields={
                'hdr.ipv4.srcAddr': entry["match"]["srcIpAddr"],
                'hdr.tcp.srcPort': entry["match"]["srcTcpPort"],
                'hdr.tcp.dstPort': entry["match"]["dstTcpPort"],
            },
            action_name='MyIngress.snat_a',
            action_params={
                'dstIpAddr': entry["params"]["dstIpAddr"],
                'dstMacAddr': entry["params"]["dstMacAddr"],
                'srcIpAddr': entry["params"]["srcIpAddr"],
                'srcPort': entry["params"]["srcPort"],
                'egress_port': entry["params"]["egress_port"],
                'dstPort': entry["params"]["dstPort"]
            }
        )
        self.bmv2_sw.WriteTableEntry(table_entry=table_entry)


    def add_reverse_snat_table_entry(self, entry: dict):
        table_entry = self.p4i_helper.buildTableEntry(
            table_name='MyIngress.reverse_snat_t',
            match_fields={
                'hdr.tcp.dstPort': entry["match"]["dstPort"],
            },
            action_name='MyIngress.reverse_snat_a',
            action_params={
                'dstIpAddr': entry["params"]["dstIpAddr"],
                'dstPort': entry["params"]["dstPort"],
                'dstMacAddr': entry["params"]["dstMacAddr"],
                'srcIpAddr': entry["params"]["srcIpAddr"],
                'egress_port': entry["params"]["egress_port"],
            }
        )

        
        self.bmv2_sw.WriteTableEntry(table_entry=table_entry)

    
    def add_service_table_entry(self, port: int):
        table_entry = self.p4i_helper.buildTableEntry(
            table_name='MyIngress.service',
            match_fields={
                'hdr.tcp.dstPort': port,
            },
            action_name='MyIngress.no_action',
        )

        self.bmv2_sw.WriteTableEntry(table_entry=table_entry)

    def add_port_mapping(self, ip, user_port):
        if not self.available_ports or len(self.available_ports) == 0:
            raise ValueError("No available ports to map.")

        port = random.choice(self.available_ports)
        if is_port_in_use(port):
            port = random.choice(self.available_ports)

        self.port_map[port] = (ip, user_port)
        self.available_ports.remove(port)
        add_iptables_rule(port)
        return port
    
    def check_address_exists(self, ip_address, port):
        for value in self.port_map.values():
            if value[0] == ip_address and value[1] == port:
                return True
        return False


    def receivePacketsFromDataplane(self):
        """
        - Create a thread for each received packet  
        """
        print('[✅] Waiting to receive packets from dataplane ...')
        for stream_msg_response in self.bmv2_sw.stream_msg_resp:

            result = protobuf_to_dict(stream_msg_response)
            ether = Ether(result["packet"]["payload"])
            packet = ether.payload
            datagram = packet.payload
            
            if self.check_address_exists(packet.src, datagram.sport):
                print(f"user with ip: {packet.src}:{datagram.sport} already exist")
                continue

            # Here add load balancer to choose a server from available servers for that service
            server = self.load_balancer.get_next_server(datagram.dport) 
            
            new_user_port = self.add_port_mapping(packet.src, datagram.sport)
             
            snat_entry = {
                'match': {
                    'srcIpAddr': packet.src,
                    'srcTcpPort': datagram.sport,
                    'dstTcpPort': 8000,
                },
                'params': {
                    'dstIpAddr': server['ip'],
                    'dstMacAddr': BMV2_SWITCH['gateway_interface']['mac'],
                    'srcIpAddr': BMV2_SWITCH['cluster_interfaces'][0]['private_ip'],
                    'srcPort': new_user_port,  
                    'egress_port': server['connected_to_sw_port'],
                    'dstPort': server['port']
                }
            }
            
            self.add_snat_table_entry(snat_entry)
            
            reverse_snat_entry = {
                'match': { 'dstPort': new_user_port },
                'params': {
                    'dstIpAddr': packet.src,
                    'dstPort': datagram.sport,
                    'dstMacAddr': BMV2_SWITCH['gateway_interface']['mac'],
                    'srcIpAddr': BMV2_SWITCH['users_interface']['public_ip'],
                    'egress_port': BMV2_SWITCH["users_interface"]["switch_port"]
                }
            }        
            self.add_reverse_snat_table_entry(reverse_snat_entry)
            print("A new user have connected with ip: {} and port: {}".format(packet.src, datagram.sport))

    def shutdown(self):
        ShutdownAllSwitchConnections()

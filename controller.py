
from config import *
from helpers import *

from p4runtime_lib.switch import ShutdownAllSwitchConnections
from p4runtime_lib import bmv2, helper
from protobuf_to_dict import protobuf_to_dict
import grpc
from scapy.all import *


class Controller:
    def __init__(self, p4i_file_path=BMV2_SWITCH['p4i_file_path'], bmv2_json_file_path=BMV2_SWITCH['json_file_path']) -> None:

        self.p4i_helper = helper.P4InfoHelper(p4i_file_path)
        
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

        
        self.add_service_table_entry(port=8000)

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
            }
        )
        self.bmv2_sw.WriteTableEntry(able_entry=table_entry)


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

    def receivePacketsFromDataplane(self):
        print('[✅] Waiting to receive packets from dataplane ...')
        for stream_msg_response in self.bmv2_sw.stream_msg_resp:
            result = protobuf_to_dict(stream_msg_response)
            ether = Ether(result["packet"]["payload"])
            packet = ether.payload
            datagram = packet.payload

            # Here add load balancer to choose a server from available servers for that service
            server = services[0]['servers'][0]
            
            snat_entry = {
                'match': {
                    'srcIpAddr': packet.src,
                    'srcTcpPort': datagram.sport,
                    'dstTcpPort': datagram.dport,
                },
                'params': {
                    'dstIpAddr': server['ip'],
                    'dstMacAddr': BMV2_SWITCH['gateway_interface']['mac'],
                    'srcIpAddr': BMV2_SWITCH['cluster_interfaces'][0]['private_ip'],
                    'srcPort': datagram.sport,  
                    'egress_port': server['connected_to_sw_port']
                }
            }
            
            self.add_snat_table_entry(snat_entry)
            
            reverse_snat_entry = {
                'match': { 'dstPort': datagram.sport },
                'params': {
                    'dstIpAddr': str(packet.src),
                    'dstPort': str(datagram.sport),
                    'dstMacAddr': BMV2_SWITCH['gateway_interface']['mac'],
                    'srcIpAddr': BMV2_SWITCH['users_interface']['public_ip'],
                    'egress_port': BMV2_SWITCH["users_interface"]["switch_port"]
                }
            }        
            self.add_reverse_snat_table_entry(reverse_snat_entry)


    def shutdown(self):
        ShutdownAllSwitchConnections()

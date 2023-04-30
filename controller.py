
import argparse
import sys
import os
import grpc
from time import sleep
import binascii 


sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

from p4runtime_lib.switch import ShutdownAllSwitchConnections
from p4runtime_lib.bmv2 import Bmv2SwitchConnection
from p4runtime_lib.helper import P4InfoHelper
from p4runtime_lib import bmv2, helper
from p4.tmp import p4config_pb2
from p4.v1 import p4runtime_pb2, p4runtime_pb2_grpc
from protobuf_to_dict import protobuf_to_dict, dict_to_protobuf

BMV2_SWITCH = {
    'id': 0,
    'server_addr': '127.0.0.1:9559',
    'users_interface': {
        'port': 0,
        'mac': '42:01:0a:c8:00:04'
    },
    'cluster_interfaces': [{
        'port': 1,
        'mac': '42:01:0a:c6:00:05'
    }
    ],
    'proto_dump_file': 'logs/p4runtime-requests.txt',
    'p4i_file_path': './build/lb.p4.p4info.txt',
    'json_file_path': './build/lb.json',
}


def add_send_frame_table_entry(p4i_helper: P4InfoHelper,
                               bmv2_sw: Bmv2SwitchConnection,
                               port: int, mac_addr: str):
    table_entry = p4i_helper.buildTableEntry(
        table_name='MyEgress.send_frame',
        match_fields={
            'standard_metadata.egress_spec': port
        },
        action_name='MyEgress.rewrite_mac',
        action_params={
            'smac': mac_addr
        }
    )

    bmv2_sw.WriteTableEntry(table_entry=table_entry)


def add_ecmp_table_entry(p4i_helper: P4InfoHelper,
                         bmv2_sw: Bmv2SwitchConnection,
                         port: int, group_id: int,
                         number_of_ecmp_path: int 
                        ):
    table_entry = p4i_helper.buildTableEntry(
        table_name='MyIngress.ecmp_group',
        match_fields={
            'hdr.tcp.dstPort': port
        },
        action_name='MyIngress.set_ecmp_group',
        action_params={
            'group_id': group_id,
            'number_of_ecmp_path': number_of_ecmp_path
        }
    )
    bmv2_sw.WriteTableEntry(table_entry=table_entry)


def add_snat_table_entry(p4i_helper: P4InfoHelper,
                        bmv2_sw: Bmv2SwitchConnection,
                        entry: dict
                        ):
    table_entry = p4i_helper.buildTableEntry(
        table_name='MyIngress.snat_t',
        match_fields={
            'meta.ecmp_group_id': entry["match"]["group_id"],
            'meta.ecmp_path_id': entry["match"]["path_id"]
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
    bmv2_sw.WriteTableEntry(table_entry=table_entry)


def add_reverse_snat_table_entry(p4i_helper: P4InfoHelper,
                        bmv2_sw: Bmv2SwitchConnection,
                        entry: dict
                        ):
    table_entry = p4i_helper.buildTableEntry(
        table_name='MyIngress.reverse_snat_t',
        match_fields={
            'hdr.tcp.dstPort': entry["match"]["tcpDstPort"],
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

    bmv2_sw.WriteTableEntry(table_entry=table_entry)
    

def init_bmv2_tables(p4i_helper: P4InfoHelper, bmv2_sw: Bmv2SwitchConnection):

    add_send_frame_table_entry(p4i_helper, bmv2_sw,
                               port=BMV2_SWITCH["users_interface"]["port"],
                               mac_addr=BMV2_SWITCH["users_interface"]["mac"])

    for c_if in BMV2_SWITCH["cluster_interfaces"]:
        add_send_frame_table_entry(p4i_helper, bmv2_sw,
                                   port=c_if["port"],
                                   mac_addr=c_if["mac"])


def readTableRules(p4info_helper: P4InfoHelper, bmv2_sw: Bmv2SwitchConnection):
    """
    Reads the table entries from all tables on the switch.
    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    """
    print('\n----- Reading tables rules for %s -----' % bmv2_sw.name)
    for response in bmv2_sw.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            table_name = p4info_helper.get_tables_name(entry.table_id)
            print('%s: ' % table_name, end=' ')
            print()


def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))


def packet_in(bmv2_sw: Bmv2SwitchConnection):
    print('[✅] Waiting to receive packets from dataplane ...')
    for response in bmv2_sw.stream_msg_resp:
        print('[✅] A message has been received')
        t = protobuf_to_dict(response)
        print(type(t))
        print(t)

def main(p4i_file_path, bmv2_json_file_path):

    p4i_helper = helper.P4InfoHelper(p4i_file_path)

    try:
        bmv2_sw = bmv2.Bmv2SwitchConnection(
            address=BMV2_SWITCH['server_addr'],
            device_id=BMV2_SWITCH['id'],
            proto_dump_file=BMV2_SWITCH['proto_dump_file'],
        )

        bmv2_sw.MasterArbitrationUpdate()

        bmv2_sw.SetForwardingPipelineConfig(p4info=p4i_helper.p4info,
                                            bmv2_json_file_path=bmv2_json_file_path)
        print(
            "[✅] Installed loadbalancer P4 Program using SetForwardingPipelineConfig on the switch.")

        #init_bmv2_tables(p4i_helper, bmv2_sw)
        #print("[✅] BMv2 switch tables were intialized successfully.")

        #readTableRules(p4i_helper, bmv2_sw)
        

        table_entry = p4i_helper.buildTableEntry(
            table_name='MyIngress.ecmp_group',
            match_fields={
                'hdr.tcp.dstPort': 55555,
            },
            action_name='MyIngress.set_ecmp_group',
            action_params={
                'group_id': 55555,
                'number_of_ecmp_path': 1,
            }
        )
        bmv2_sw.WriteTableEntry(table_entry=table_entry)

        packet_in(bmv2_sw=bmv2_sw)

    except KeyboardInterrupt:
        print("[!] Shutting down.")

    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()


if __name__ == '__main__':
    main(p4i_file_path=BMV2_SWITCH['p4i_file_path'],
         bmv2_json_file_path=BMV2_SWITCH['json_file_path'])

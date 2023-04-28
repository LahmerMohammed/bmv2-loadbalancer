import argparse
import sys
import os
import grpc
from time import sleep
from p4.tmp import p4config_pb2
from p4.v1 import p4runtime_pb2, p4runtime_pb2_grpc



sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))

from p4runtime_lib import bmv2, helper
from p4runtime_lib.helper import P4InfoHelper
from p4runtime_lib.bmv2 import Bmv2SwitchConnection
from p4runtime_lib.switch import ShutdownAllSwitchConnections


BMV2_SWITCH={
    'id': 0,
    'server_addr': '127.0.0.1:9559',
    'switch_to_users_if': {
        'port': 0,
        'mac': '42:01:0a:c8:00:04'
    },
    'switch_to_cluster_if': {
        'port': 1,
        'mac': '42:01:0a:c6:00:05'
    },
}

def init_bmv2_tables(p4i_helper: P4InfoHelper, bmv2_sw: Bmv2SwitchConnection):

    table_entry = p4i_helper.buildTableEntry(
        table_name='MyEgress.send_frame',
        match_fields={
            'standard_metadata.egress_spec': BMV2_SWITCH["switch_to_users_if"]["port"]
        },
        action_name='MyEgress.rewrite_mac',
        action_params={
            'smac': BMV2_SWITCH["switch_to_users_if"]["mac"]
        }
    )

    bmv2_sw.WriteTableEntry(table_entry, dry_run=True)

    table_entry = p4i_helper.buildTableEntry(
        table_name='MyEgress.send_frame',
        match_fields={
            'standard_metadata.egress_spec': BMV2_SWITCH["switch_to_cluster_if"]["port"]
        },
        action_name='MyEgress.rewrite_mac',
        action_params={
            'smac': BMV2_SWITCH["switch_to_cluster_if"]["mac"]
        }
    )
    
    bmv2_sw.WriteTableEntry(table_entry, dry_run=True)



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

def receivePacketFromDataPlane(bmv2_sw: Bmv2SwitchConnection):
    for response in bmv2_sw.stream_msg_resp:
        pass


def packet_in(bmv2_sw: Bmv2SwitchConnection):
    print('[✅] Waiting to receive packets from dataplane ...')
    for response in bmv2_sw.stream_msg_resp:
        print('[✅] A message has been received')
        print(response)
    
def main(p4i_file_path, bmv2_json_file_path):

    p4i_helper = helper.P4InfoHelper(p4i_file_path)

    try:
        bmv2_sw = bmv2.Bmv2SwitchConnection(
            address=BMV2_SWITCH['server_addr'],
            device_id=BMV2_SWITCH['id'],
            proto_dump_file='logs/p4runtime-requests.txt',
        )

        bmv2_sw.MasterArbitrationUpdate()

        bmv2_sw.SetForwardingPipelineConfig(p4info=p4i_helper.p4info, 
                                            bmv2_json_file_path=bmv2_json_file_path)
        print("[✅] Installed loadbalancer P4 Program using SetForwardingPipelineConfig on the switch.")


        init_bmv2_tables(p4i_helper, bmv2_sw)
        print("[✅] BMv2 switch tables were intialized successfully.")


        readTableRules(p4i_helper, bmv2_sw)

        receivePacketFromDataPlane(bmv2_sw=bmv2_sw)

    except KeyboardInterrupt:
        print("[!] Shutting down.")

    except grpc.RpcError as e:
        printGrpcError(e)
    
    ShutdownAllSwitchConnections()


if __name__ == '__main__':
    main(p4i_file_path='./build/lb.p4.p4info.txt',bmv2_json_file_path='./build/lb.json' )
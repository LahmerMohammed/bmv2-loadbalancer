import argparse
import sys
import os
import grpc
from time import sleep
from p4runtime_lib import bmv2, helper
from p4runtime_lib.helper import P4InfoHelper
from p4runtime_lib.bmv2 import Bmv2SwitchConnection
from p4runtime_lib.switch import ShutdownAllSwitchConnections


sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils'))


P4RUNTIME_SERVER_PORT = 9559
SWITCH_TO_USERS_PORT = 0
SWITCH_TO_CLUSTER_PORT = 1

def init_bmv2_tables(p4i_helper: P4InfoHelper, bmv2_sw: Bmv2SwitchConnection):

    table_entry = p4i_helper.buildTableEntry(
        table_name='MyEgress.send_frame',
        match_fields={
            'standard_metadata.egress_spec': SWITCH_TO_USERS_PORT
        },
        action_name='rewrite_mac',
        action_params={
            'smac': '42:01:0a:c8:00:04'
        }
    )

    bmv2_sw.WriteTableEntry(table_entry, dry_run=True)

    table_entry = p4i_helper.buildTableEntry(
        table_name='MyEgress.send_frame',
        match_fields={
            'standard_metadata.egress_spec': SWITCH_TO_CLUSTER_PORT
        },
        action_name='rewrite_mac',
        action_params={
            'smac': '42:01:0a:c6:00:05'
        }
    )

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
            for m in entry.match:
                print(p4info_helper.get_match_field_name(table_name, m.field_id), end=' ')
                print('%r' % (p4info_helper.get_match_field_value(m),), end=' ')
            action = entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print('->', action_name, end=' ')
            for p in action.params:
                print(p4info_helper.get_action_param_name(action_name, p.param_id), end=' ')
                print('%r' % p.value, end=' ')
            print()


def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))


def main(p4i_file_path, bmv2_json_file_path):

    p4i_helper = helper.P4InfoHelper(p4i_file_path)

    try:
        bmv2_sw = bmv2.Bmv2SwitchConnection(
            name='loadbalancer',
            address='127.0.0.1:{}'.format(P4RUNTIME_SERVER_PORT),
            device_id=0,
            proto_dump_file='logs/p4runtime-requests.txt',
        )

        bmv2_sw.MasterArbitrationUpdate()


        bmv2_sw.SetForwardingPipelineConfig(p4info=p4i_helper.p4info, 
                                            bmv2_json_file_path=bmv2_json_file_path)
        print("[✅] Installed loadbalancer P4 Program using SetForwardingPipelineConfig on the switch.")


        init_bmv2_tables(p4i_helper, bmv2_sw)
        print("[✅] BMv2 switch tables were intialized successfully.")


        readTableRules(p4i_helper, bmv2_sw)

        # Print the tunnel counters every 2 seconds
        while True:
            sleep(5)

    except KeyboardInterrupt:
        print("[!] Shutting down.")

    except grpc.RpcError as e:
        printGrpcError(e)
    
    ShutdownAllSwitchConnections()


if __name__ == 'main':
    main(p4i_file_path='./build/lb.p4i',bmv2_json_file_path='./build/lb.json' )

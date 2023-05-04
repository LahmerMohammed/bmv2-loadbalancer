import sys

sys.path.append('./utils')

services = [
    {
        'id': 1,
        'name': 'tcp_server',
        'port': 8000,
        'servers': [
            {
                'id': 1,
                'ip': '10.198.0.2',
                'connected_to_sw_port': 1,
            }
        ],
    },
    {
        'id': 2,
        'name': 'yolo_model',
        'port': 9000,
        'servers': [
            {
                'id': 1,
                'ip': '10.198.0.2',
                'connected_to_sw_port': 1,
            }   
        ]
    },

]


BMV2_SWITCH = {
    'id': 0,
    'server_addr': '127.0.0.1:9559',
    'users_interface': {
        'switch_port': 0,
        'mac': '42:01:0a:c8:00:04',
        'public_ip': '34.154.94.220',
    },
    'cluster_interfaces': [{
        'switch_port': 1,
        'mac': '42:01:0a:c6:00:05',
        'private_ip': '10.198.0.5'
    }
    ],
    'gateway_interface': {
        'mac': '42:01:0a:c6:00:01',
    },
    'proto_dump_file': 'logs/p4runtime-requests.txt',
    'p4i_file_path': './build/lb.p4.p4info.txt',
    'json_file_path': './build/lb.json',
}

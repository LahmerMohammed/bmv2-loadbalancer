import sys

sys.path.append('./utils')

services = {
    8000: {
        'name': 'tcp_server',
        'port': 8000,
        'servers': [
            {
                'ip': '10.198.0.2',
                'connected_to_sw_port': 1,
            }
        ],
    },
    9000: {
        'name': 'yolo_model',
        'port': 9000,
        'servers': [
            {
                'ip': '10.198.0.2',
                'connected_to_sw_port': 1,
            }   
        ]
    },
}


BMV2_SWITCH = {
    'id': 0,
    'server_addr': '127.0.0.1:9559',
    'users_interface': {
        'switch_port': 0,
        'mac': '42:01:0a:c6:00:0d',
        'public_ip': '34.154.187.246',
    },
    'cluster_interfaces': [{
        'switch_port': 1,
        'mac': '42:01:ac:14:00:08',
        'private_ip': '172.20.0.8'
    }
    ],
    'gateway_interface': {
        'mac': '42:01:0a:c6:00:01',
    },
    'proto_dump_file': 'logs/p4runtime-requests.txt',
    'p4i_file_path': './build/lb.p4.p4info.txt',
    'json_file_path': './build/lb.json',
}

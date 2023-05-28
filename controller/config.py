import sys

sys.path.append('./utils')

services = {
    8000: {
        'name': 'yolo_model',
        'servers': [
            {
                'ip': '10.198.0.11',
                'connected_to_sw_port': 1,
                'port': '30946',
                'pod_id': '2',
            }, 
            {
                'ip': '10.198.0.11',
                'connected_to_sw_port': 1,
                'port': '30948',
                'pod_id': '1',
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
        'public_ip': '34.154.207.50',
    },
    'cluster_interfaces': [{
        'switch_port': 1,
        'mac': '42:01:ac:14:00:08',
        'private_ip': '10.198.0.13'
    }
    ],
    'gateway_interface': {
        'mac': '42:01:0a:c6:00:01',
    },
    'proto_dump_file': 'logs/p4runtime-requests.txt',
    'p4i_file_path': './build/lb.p4.p4info.txt',
    'json_file_path': './build/lb.json',
}

import sys
sys.path.append('./utils')

from kubernetes import client, config

# Load the Kubernetes configuration
config.load_kube_config()

# Create an instance of the Kubernetes API client
api_client = client.CoreV1Api()



def get_services():
    # Retrieve and filter NodePort services
    nodeports = [
        service for service in api_client.list_service_for_all_namespaces().items
        if service.spec.type == "NodePort"
    ]



    services = {
        8000: {
            'name': 'ml_model',
            'servers': []
        },
    }

    for node_port in nodeports:
        service_ports = node_port.spec.ports[0]

        if service_ports.port not in services:
            services[service_ports.port] = {
                'name': node_port.metadata.name,
                'servers': []
            }

        services[service_ports.port]['servers'].append({
            'id': node_port.metadata.uid,
            'ip': '10.10.1.1',
            'connected_to_sw_port': 1,
            'port': service_ports.node_port
        })
    return services


BMV2_SWITCH = {
    'id': 0,
    'server_addr': '127.0.0.1:9559',
    'users_interface': {
        'switch_port': 0,
        'mac': 'ec:b1:d7:85:2a:b2',
        'public_ip': '128.110.217.245',
    },
    'cluster_interfaces': [{
        'switch_port': 1,
        'mac': 'ec:b1:d7:85:2a:b3',
        'private_ip': '10.10.1.2'
    }
    ],
    'gateway_interface': {
        'mac_eno1': '18:5a:58:34:49:e4',
        'mac_eno1d1': '14:58:d0:58:ff:83'
        
    },
    'proto_dump_file': 'logs/p4runtime-requests.txt',
    'p4i_file_path': './build/lb.p4.p4info.txt',
    'json_file_path': './build/lb.json',
}

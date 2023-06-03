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
            'ip': '10.198.0.11',
            'connected_to_sw_port': 1,
            'port': service_ports.node_port
        })



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

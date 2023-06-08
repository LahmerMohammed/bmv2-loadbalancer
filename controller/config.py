import sys
sys.path.append('./utils')

from kubernetes import client, config

# Load the Kubernetes configuration
config.load_kube_config()

# Create an instance of the Kubernetes API client
api_client = client.CoreV1Api()

PODS = {
        31111: {"id": "285a4c46-eba3-4d9e-b7d8-2d3d6cab3776", "cpu_limit": 3},
    31112: {"id": "79d8a49b-db77-4eaa-814a-55583222ac32", "cpu_limit": 7}

}


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
            'port': service_ports.node_port,
            'pod_id': PODS[service_ports.node_port]["id"],
            'cpu_limit': PODS[service_ports.node_port]["cpu_limit"],

        })
    return services


BMV2_SWITCH = {
    'id': 0,
    'server_addr': '127.0.0.1:9559',
    'users_interface': {
        'switch_port': 0,
        'mac': '14:58:d0:58:4f:22',
        'public_ip': '128.110.217.252',
    },
    'cluster_interfaces': [{
        'switch_port': 1,
        'mac': '14:58:d0:58:4f:23',
        'private_ip': '10.10.1.2'
    }
    ],
    'gateway_interface': {
        'mac_eno1': '18:5a:58:34:49:e4',
        'mac_eno1d1': '14:58:d0:58:ff:a3'
        
    },
    'proto_dump_file': 'logs/p4runtime-requests.txt',
    'p4i_file_path': './build/lb.p4.p4info.txt',
    'json_file_path': './build/lb.json',
}

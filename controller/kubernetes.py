from kubernetes import client, config

# Load the Kubernetes configuration
config.load_kube_config()

# Create an instance of the Kubernetes API client
api_client = client.ApiClient()


api_endpoint = "/apis/metrics.k8s.io/v1beta1"


def get_pod_stat(pod_name: str, namespace="default"):
    endpoint = '{}/namespaces/{}/pods/{}'.format(api_endpoint, namespace, pod_name)
    # response shape: tuple(data, http-status, http-header)
    response = api_client.call_api(endpoint, "GET", response_type="object")

    data = response[0]

    return data

def get_all_pods_stats(namespace="default"):
    endpoint = '{}/namespaces/{}/pods'.format(api_endpoint, namespace)
    # response shape: tuple(data, http-status, http-header)
    response = api_client.call_api(endpoint, "GET", response_type="object")

    data = response[0]

    return data
    


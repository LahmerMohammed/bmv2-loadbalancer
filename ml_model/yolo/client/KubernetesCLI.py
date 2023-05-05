from kubernetes import client, config

# Load the Kubernetes configuration
config.load_kube_config()

# Create an instance of the Kubernetes API client
api_client = client.ApiClient()


api_endpoint = "/apis/metrics.k8s.io/v1beta1"


class Kubernetes:
    def __init__(self):
        config.load_kube_config()
        self.api_client = client.ApiClient()
        self.api_endpoint = "/apis/metrics.k8s.io/v1beta1"

    def get_pod_stat(self, pod_name: str, namespace="default"):
        endpoint = '{}/namespaces/{}/pods/{}'.format(
            self.api_endpoint, namespace, pod_name)

        # response shape: tuple(data, http-status, http-header)
        response = self.api_client.call_api(
            endpoint, "GET", response_type="object")

        data = response[0]

        return data

    def get_all_pods_stats(self, namespace="default"):
        endpoint = '{}/namespaces/{}/pods'.format(api_endpoint, namespace)
        # response shape: tuple(data, http-status, http-header)
        response = self.api_client.call_api(
            endpoint, "GET", response_type="object")

        data = response[0]

        return data

    def update_pod_resources(self, pod_name: str, cpu_limit: str, mem_limit: str, namespace="default"):
        # Get the current pod definition
        pod = self.api_client.read_namespaced_pod(
            name=pod_name, namespace=namespace)

        # Update the pod definition with the new resource requirements
        pod.spec.containers[0].resources.limits["cpu"] = cpu_limit
        pod.spec.containers[0].resources.limits["memory"] = mem_limit

        # Update the pod in Kubernetes
        self.api_client.replace_namespaced_pod(
            name=pod_name, namespace=namespace, body=pod, pretty=True)

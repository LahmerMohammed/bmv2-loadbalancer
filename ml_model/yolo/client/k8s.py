from kubernetes import client, config
import kubernetes
import yaml

api_endpoint = "/apis/metrics.k8s.io/v1beta1"


class KubernetesCLI:
    def __init__(self):

        # Create an instance of the Kubernetes API client
        self.api_client = client.ApiClient(self.configuration)
        self.api_endpoint = "/apis/metrics.k8s.io/v1beta1"
        self.api_instance = kubernetes.client.CoreV1Api(self.api_client)

    def get_pod_stat(self, pod_name: str, namespace="default"):
        endpoint = '{}/namespaces/{}/pods/{}'.format(
            self.api_endpoint, namespace, pod_name)

        # response shape: tuple(data, http-status, http-header)
        response = self.api_client.call_api(
            endpoint, "GET", response_type="object")
        
        if response.status_code != 200:
            return None
        
        data = response[0]
        return data


    def get_all_pods_stats(self, namespace="default"):
        endpoint = '{}/namespaces/{}/pods'.format(api_endpoint, namespace)
        # response shape: tuple(data, http-status, http-header)
        response = self.api_client.call_api(
            endpoint, "GET", response_type="object")

        data = response[0]

        return data
    

    def delete_pod(self, pod_name: str, namespace="default"):
        response = self.api_instance.delete_namespaced_pod(pod_name, namespace=namespace)
        if response.status_code == 200:
            return response
        else:
            return None

    def create_pod(self, yaml_file: str,  cpu: str=None, namespace="default"):
        with open(yaml_file) as f:
            pod_yaml = yaml.safe_load(f)
        
        pod_yaml['spec']['containers'][0]['resources']['limits'] = {
            "cpu": cpu,
        }

        
        response = self.api_instance.create_namespaced_pod(body=pod_yaml, namespace=namespace)

        if response.status_code == 200:
            return response
        else:
            return None
    

    def get_pod_status(self, pod_name: str, namespace="default"):

        pod_status = self.api_instance.read_namespaced_pod_status(pod_name, namespace=namespace)

        return pod_status.status.phase
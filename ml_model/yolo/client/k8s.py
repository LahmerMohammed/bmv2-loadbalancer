from kubernetes import client, config
import kubernetes
import yaml
from kubernetes.client.rest import ApiException

api_endpoint = "/apis/metrics.k8s.io/v1beta1"


class KubernetesCLI:
    def __init__(self):
        # Load the Kubernetes configuration
        config.load_kube_config()
        # Create an instance of the Kubernetes API client
        self.api_client = client.ApiClient()
        self.api_endpoint = "/apis/metrics.k8s.io/v1beta1"
        self.api_instance = kubernetes.client.CoreV1Api(self.api_client)

    def get_pod_stat(self, pod_name: str, namespace="default"):
        endpoint = '{}/namespaces/{}/pods/{}'.format(
            self.api_endpoint, namespace, pod_name)
        try: 
        # response shape: tuple(data, http-status, http-header)
            response = self.api_client.call_api(
                endpoint, "GET", response_type="object")
            data = response[0]
            return data
        except ApiException as e: 
            print(e)   
            return None
        
        

    def get_all_pods_stats(self, namespace="default"):
        endpoint = '{}/namespaces/{}/pods'.format(api_endpoint, namespace)
        # response shape: tuple(data, http-status, http-header)
        response = self.api_client.call_api(
            endpoint, "GET", response_type="object")

        data = response[0]

        return data
    

    def delete_pod(self, pod_name: str, namespace="default"):
        try:
            response = self.api_instance.delete_namespaced_pod(pod_name, namespace=namespace)
        except ApiException as e:
            return None

    def create_pod(self, yaml_file: str,  cpu: str=None, namespace="default"):
        with open(yaml_file) as f:
            pod_yaml = yaml.safe_load(f)
        
        pod_yaml['spec']['containers'][0]['resources']['limits'] = {
            "cpu": cpu,
        }

        try:        
            response = self.api_instance.create_namespaced_pod(body=pod_yaml, namespace=namespace)
            return response
        except ApiException as e:
            return None

    def get_pod_status(self, pod_name: str, namespace="default"):

        pod_status = self.api_instance.read_namespaced_pod_status(pod_name, namespace=namespace)

        return pod_status.status.phase
    def pod_exists(self, name, namespace="default"):

        try:
        # Get pod by name and namespace
            self.api_instance.read_namespaced_pod(name, namespace)
            return True
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return False
            else:
                raise e

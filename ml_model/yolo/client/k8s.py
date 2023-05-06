from kubernetes import client, config
import kubernetes
import yaml

api_endpoint = "/apis/metrics.k8s.io/v1beta1"


class Kubernetes:
    def __init__(self, host: str=None, token: str= None):

        self.configuration = client.Configuration()
        self.configuration.host = "https://34.154.157.82:6443"
        self.configuration.verify_ssl = False
        self.configuration.api_key = {"authorization": "Bearer " + token}

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
        pod = self.api_instance.read_namespaced_pod(
            name=pod_name, namespace=namespace)

        # Update the pod definition with the new resource requirements
        pod.spec.containers[0].resources.limits = {
            "cpu": cpu_limit,
            "memory": mem_limit,
        }

        # Update the pod in Kubernetes
        self.api_instance.replace_namespaced_pod(
            name=pod_name, namespace=namespace, body=pod, pretty=True)

    def delete_pod(self, pod_name: str, namespace="default"):
        self.api_instance.delete_namespaced_pod(pod_name, namespace=namespace)

    def create_pod(self, yaml_file: str, namespace="default"):
        with open(yaml_file) as f:
            pod_yaml = yaml.safe_load(f)
        
        pod_yaml['spec']['containers'][0]['resources']['limits'] = {
            "cpu": "1027090n",
            "memory": "105255352n",
        }

        
        response = self.api_instance.create_namespaced_pod(body=pod_yaml, namespace=namespace)
        return response
if __name__ == "__main__":
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ik1HSi11NGtlclRXbmJPZERCOEpFLUg4dmhoYWY5NUdZN2s5NFo3S1Z3bVUifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4iLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjIyZjE5MTdiLWM4YTMtNDEyYy1iMjQ3LWI1YmRiY2UxN2RkMiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.RlAOMJrVN74blZTUiS--dy06XTyrqFEF9JtxfHojZQ9gRgLqOyveDVBuCJdIWDeVo3lXbJpsPcGIyN2HFlXkq-Zrf0YSlzf4dRXh2RmO85zHv4F7EKftYVeC8Um2y41F_fcJ95oFKahu8j8e7Vx_C7a073_VjjeafgWt7J-Nw89iIi6ZNlJwaEUdj023Sd_uHZ60edNdWD4OHyYXtRVDQ_ASx_TBjR8EhVGGMaXKeihk6spOQI39ZbWIL6okcYaSWSdLJfoCy8anbxI8IO225Ms4Al6JXr0iFi4bmwLAcoCARrFQJrfdiMv8HXxTFSnDkhnETDaKDMpRW4TB5z2tig"
    host = "https://34.154.157.82:6443"
    
    kubernetes = Kubernetes(host=host, token=token)

    #response = kubernetes.update_pod_resources(pod_name="yolo-v3", mem_limit="360000Ki", cpu_limit="20000000n")
    #response = kubernetes.delete_pod(pod_name="yolo-v3")
    #print(response)

    response = kubernetes.create_pod(yaml_file='../templates/pod.yaml')
    print(response)

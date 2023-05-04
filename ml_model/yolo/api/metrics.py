from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST, Metric, Summary
from prometheus_client.samples import Sample

""""""

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

REQUEST_COUNT = Counter(
    "request_count",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)


# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds',
                       'Time spent processing request')
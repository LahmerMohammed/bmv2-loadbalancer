import os
import time
import re
from fastapi import FastAPI, HTTPException
import threading
import signal
import sys

app = FastAPI()

STATS = {}
STOP_THREAD = False


pod_id_regex = r'.*pod(.{0,})'

cpu_cgroup_dir = '/sys/fs/cgroup/cpuacct/kubepods'
memory_cgroup_dir = '/sys/fs/cgroup/memory/kubepods'

#/sys/fs/cgroup/memory/kubepods/burstable/pod91322901-a432-4b75-a793-d9742983d275/memory.usage_in_bytes 

pod_slice_dirs = [dir for dir in os.listdir(
    cpu_cgroup_dir) if dir.startswith('burstable') ]

def get_pod_per_cpu_stat(pod_path: str, cpu_quota_s, cpu_period_s, interval_resolution_s=1):
    per_cpu_usage_path = 'cpuacct.usage_percpu'
    memory_usage_path = "memory.usage_in_bytes" 

    with open(os.path.join(pod_path, per_cpu_usage_path), 'r') as f:
        start_s = time.time()
        initial_per_cpu_usage_s = [
            float(x)/1000_000_000 for x in f.read().strip().split(' ')]
        

    time.sleep(interval_resolution_s)

    with open(os.path.join(pod_path, per_cpu_usage_path), 'r') as f:
        end_s = time.time()
        updated_per_cpu_usage_s = [
            float(x)/1000_000_000 for x in f.read().strip().split(' ')]
    
    with open(os.path.join(pod_path.replace('cpuacct', 'memory'), memory_usage_path), 'r') as f:
        memory_usage_kb = float(f.read().strip()) / 1000

    elapsed_time_s = end_s - start_s
    per_cpu_usage_percentage = []

    for i in range(len(initial_per_cpu_usage_s)):
        per_cpu_usage_percentage.append(
            (updated_per_cpu_usage_s[i] - initial_per_cpu_usage_s[i]
             ) * cpu_period_s / elapsed_time_s / cpu_quota_s * 100
        )
    
    return (per_cpu_usage_percentage, memory_usage_kb)


def scrape_pod_cpu_memory_usage():
    global pod_id_regex
    global cpu_cgroup_dir
    global STATS
    global pod_slice_dirs

    pod_dirs = []

    for dir in pod_slice_dirs:
        pds = os.listdir(os.path.join(cpu_cgroup_dir, dir))
        pod_dirs.extend([os.path.join(dir, pod_dir)
                        for pod_dir in pds if re.match(r'pod.*', pod_dir)])
    
    for pod_dir in pod_dirs:
        pod_id = pod_dir.split('/')[1].split('.')[0].split('pod')[1]
        pod_path = os.path.join(cpu_cgroup_dir, pod_dir)
        
        try:
            with open(os.path.join(pod_path, 'cpu.cfs_quota_us'), 'r') as f:
                cpu_quota_s = float(f.read().strip()) / 1000_000

            if cpu_quota_s <= 0:
                continue

            with open(os.path.join(pod_path, 'cpu.cfs_period_us'), 'r') as f:
                cpu_period_s = float(f.read().strip()) / 1000_000
        
            if pod_id not in STATS:
                STATS[pod_id] = []
        

            per_cpu_stat, mem_sta = get_pod_per_cpu_stat(
                cpu_period_s=cpu_period_s, cpu_quota_s=cpu_quota_s, 
                pod_path=pod_path, interval_resolution_s=0.5)
            timestamp = time.time()
            STATS[pod_id].append((timestamp, per_cpu_stat, mem_sta))
        except FileNotFoundError:
            if pod_id in STATS:
                STATS.pop(pod_id)
            continue



def every(delay, task):
  try:
    while not STOP_THREAD:
        task()
        time.sleep(delay)
  except KeyboardInterrupt:
    print("Ctrl+C detected. Stopping the thread...")
    sys.exit(0)   

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=lambda: every(0.5, scrape_pod_cpu_memory_usage)).start()


# Endpoint to retrieve CPU and memory stats
@app.get('/stats/{pod_id}')
def get_stats(pod_id: str, window: int):

    data = STATS[pod_id]

    # Filter the data within the window
    current_time = time.time()
    filtered_data = [(per_cpu, mem) for ts, per_cpu, mem in data if current_time - ts <= window]
    if not filtered_data:
        raise HTTPException(
            status_code=404, detail="No data found for the specified window")


    cpu_data = [per_cpu for per_cpu, mem in filtered_data]
    mem_data = [mem for per_cpu, mem in filtered_data]

    # Extract CPU and memory usage values from the filtered data
    avg_per_cpu_usage_values = []

    num_cpu = len(cpu_data[0])
    num_items = len(cpu_data)
    for i in range(num_cpu):
        avg_per_cpu_usage_values.append(round(
            sum(subarr[i] for subarr in cpu_data) / num_items, 1))
    
    return {
        'per_cpu_usage': avg_per_cpu_usage_values,
        'cpu_usage': sum(avg_per_cpu_usage_values),
        'mem_usage': sum(mem_data) / len(mem_data)
    }

def on_shutdown():
    print("Shutting down the application...")
    STOP_THREAD = True

import atexit

# Register the on_shutdown function with atexit
atexit.register(on_shutdown)


"""
rps cpu_limit req_rate req_latency cpu min_cpu max_cpu cpu0 cpu1 cpu2 cpu3 cpu4 cpu5
1   1000m     0.94     6.02        17  0.0     67.0    14.4 3.66 0.0  53.6 28.2 0.0
1   1000m     0.94     6.09        16  16.5    16.8    0.0  36.0 0.0  0.0  63.8 0.0
""" 
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
# pod_dir = '/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod077177ed_0ed7_40e0_8106_cda5a55c9a18.slice/'

cpu_cgroup_dir = '/sys/fs/cgroup/cpuacct/kubepods'
memory_cgroup_dir = '/sys/fs/cgroup/memory/memory.usage_in_bytes'

pod_slice_dirs = [dir for dir in os.listdir(
    cpu_cgroup_dir) if dir.startswith('besteffort') or dir.startswith('burstable') ]

def get_pod_per_cpu_stat(pod_path: str, cpu_quota_s, cpu_period_s, interval_resolution_s=1):
    cpu_usage_path = 'cpuacct.usage_percpu'

    with open(os.path.join(pod_path, cpu_usage_path), 'r') as f:
        start_s = time.time()
        initial_per_cpu_usage_s = [
            float(x)/1000_000_000 for x in f.read().strip().split(' ')]

    time.sleep(interval_resolution_s)

    with open(os.path.join(pod_path, cpu_usage_path), 'r') as f:
        end_s = time.time()
        updated_per_cpu_usage_s = [
            float(x)/1000_000_000 for x in f.read().strip().split(' ')]

    elapsed_time_s = end_s - start_s

    per_cpu_usage_percentage = []

    for i in range(len(initial_per_cpu_usage_s)):
        per_cpu_usage_percentage.append(
            (updated_per_cpu_usage_s[i] - initial_per_cpu_usage_s[i]
             ) * cpu_period_s / elapsed_time_s / cpu_quota_s
        )

    return per_cpu_usage_percentage


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

        with open(os.path.join(pod_path, 'cpu.cfs_quota_us'), 'r') as f:
            cpu_quota_s = float(f.read().strip()) / 1000_000

        if cpu_quota_s <= 0:
            continue

        with open(os.path.join(pod_path, 'cpu.cfs_period_us'), 'r') as f:
            cpu_period_s = float(f.read().strip()) / 1000_000

        if pod_id not in STATS:
            STATS[pod_id] = []
        

        per_cpu_stat = get_pod_per_cpu_stat(
            cpu_period_s=cpu_period_s, cpu_quota_s=cpu_quota_s, 
            pod_path=pod_path, interval_resolution_s=0.5)
        timestamp = time.time()
        STATS[pod_id].append((timestamp, per_cpu_stat))



def every(delay, task):
  try:
    while not STOP_THREAD:
        time.sleep(delay)
        try:
            task()
        except Exception:
            traceback.print_exc()
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
    filtered_data = [cpu for ts, cpu in data if current_time - ts <= window]
    if not filtered_data:
        raise HTTPException(
            status_code=404, detail="No data found for the specified window")

    # Extract CPU and memory usage values from the filtered data
    avg_per_cpu_usage_values = []
    min_per_cpu_usage_values = []
    max_per_cpu_usage_values = []

    num_cpu = len(filtered_data[0])
    num_items = len(filtered_data)
    for i in range(num_cpu):
        avg_per_cpu_usage_values.append(
            sum(round(subarr[i], 2) for subarr in filtered_data) / num_items)
        min_per_cpu_usage_values.append(
            min(subarr[i] for subarr in filtered_data))
        max_per_cpu_usage_values.append(
            max(subarr[i] for subarr in filtered_data))

    return {
        'per_cpu_usage': avg_per_cpu_usage_values,
        'cpu_usage': round(sum(avg_per_cpu_usage_values) / len(avg_per_cpu_usage_values), 2),
        'min_cpu_usage': round(sum(min_per_cpu_usage_values) / len(min_per_cpu_usage_values), 2),
        'max_cpu_usage': round(sum(max_per_cpu_usage_values) / len(max_per_cpu_usage_values), 2)
    }

def on_shutdown():
    print("Shutting down the application...")
    STOP_THREAD = True

import atexit

# Register the on_shutdown function with atexit
atexit.register(on_shutdown)

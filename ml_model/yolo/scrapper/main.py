import os
import time
import re
from fastapi import FastAPI, HTTPException
import signal
import asyncio
import sys

app = FastAPI()

STATS = {}

lock = asyncio.Lock()

pod_id_regex = r'.*pod(.{0,})'

cpu_cgroup_dir = '/sys/fs/cgroup/cpuacct/kubepods.slice'
memory_cgroup_dir = '/sys/fs/cgroup/memory/kubepods'

#/sys/fs/cgroup/cpuacct/kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod90ec4173_930c_41c4_b302_cdf45f449f2a.slice/

pod_slice_dirs = [dir for dir in os.listdir(
    cpu_cgroup_dir) if dir.startswith('kubepods-burstable') ]

async def get_pod_per_cpu_stat(pod_path: str, cpu_quota_s, cpu_period_s, interval_resolution_s=1):
    global pod_id_regex
    global cpu_cgroup_dir
    global pod_slice_dirs

    per_cpu_usage_path = 'cpuacct.usage_percpu'
    memory_usage_path = "memory.usage_in_bytes"
    memory_limit_path = "memory.limit_in_bytes" 

    with open(os.path.join(pod_path, per_cpu_usage_path), 'r') as f:
        start_s = time.time()
        initial_per_cpu_usage_s = [
            float(x)/1000_000_000 for x in f.read().strip().split(' ')]
        
    await asyncio.sleep(interval_resolution_s)

    with open(os.path.join(pod_path, per_cpu_usage_path), 'r') as f:
        end_s = time.time()
        updated_per_cpu_usage_s = [
            float(x)/1000_000_000 for x in f.read().strip().split(' ')]
    
    with open(os.path.join(pod_path.replace('cpuacct', 'memory'), memory_usage_path), 'r') as f:
        memory_usage_mb = float(f.read().strip()) / 1000_000

    elapsed_time_s = end_s - start_s
    per_cpu_usage_percentage = []

    for i in range(len(initial_per_cpu_usage_s)):
        per_cpu_usage_percentage.append(
            (updated_per_cpu_usage_s[i] - initial_per_cpu_usage_s[i]
             ) * cpu_period_s / elapsed_time_s / cpu_quota_s * 100
        )
    
    return (per_cpu_usage_percentage, memory_usage_mb)


async def scrape_pod_cpu_memory_usage():
    global pod_id_regex
    global cpu_cgroup_dir
    global STATS
    global pod_slice_dirs

    pod_dirs = []

    for dir in pod_slice_dirs:
        pds = os.listdir(os.path.join(cpu_cgroup_dir, dir))
        pod_dirs.extend([os.path.join(dir, pod_dir)
                        for pod_dir in pds if re.match(r'.*pod.*', pod_dir)])
    
    for pod_dir in pod_dirs:
        pod_id = pod_dir.split('/')[1].split('.')[0].split('-')[2].split('pod')[1].replace('_', '-')
        pod_path = os.path.join(cpu_cgroup_dir, pod_dir)
        
        async with lock:
            try:
                with open(os.path.join(pod_path, 'cpu.cfs_quota_us'), 'r') as f:
                    cpu_quota_s = float(f.read().strip()) / 1000_000

                if cpu_quota_s <= 0:
                    continue

                with open(os.path.join(pod_path, 'cpu.cfs_period_us'), 'r') as f:
                    cpu_period_s = float(f.read().strip()) / 1000_000

                if pod_id not in STATS:
                    print(pod_id)
                    STATS[pod_id] = []


                per_cpu_usage_percentage, memory_usage_percentage = await get_pod_per_cpu_stat(
                    cpu_period_s=cpu_period_s, cpu_quota_s=cpu_quota_s, 
                    pod_path=pod_path, interval_resolution_s=0.1)
                timestamp = time.time()
                STATS[pod_id].append((timestamp, per_cpu_usage_percentage, memory_usage_percentage))
            except FileNotFoundError:
                if pod_id in STATS:
                    STATS.pop(pod_id)
                continue



async def every(delay, task):
    try:
        while True:
            await task()
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        print("Task cancelled.")
    except KeyboardInterrupt:
        print("Ctrl+C detected. Stopping the task...")
        sys.exit(0)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    task = loop.create_task(every(0.1, scrape_pod_cpu_memory_usage))

    def stop_task():
        task.cancel()

    # Register stop_task() as a cleanup function when the event loop is closed
    loop.add_signal_handler(signal.SIGINT, stop_task)
    loop.add_signal_handler(signal.SIGTERM, stop_task)


# Endpoint to retrieve CPU and memory stats
@app.get('/stats/{pod_id}')
async def get_stats(pod_id: str, window: int):
    async with lock:
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
        'cpu_usage': sum(avg_per_cpu_usage_values) if len(avg_per_cpu_usage_values) else -1,
        'memory_usage': sum(mem_data) / len(mem_data) if len(mem_data) != 0 else -1
    }

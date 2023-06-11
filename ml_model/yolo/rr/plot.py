import pandas as pd
import matplotlib.pyplot as plt

# Read the first dataset
df_model = pd.read_csv("dataset_model.csv")

# Read the second dataset
df_rr = pd.read_csv("dataset_rr.csv")

# Set the width of the bars
bar_width = 1.5

# Set the positions of the x-axis ticks
rps_ticks = df_model['RPS']

# Set the positions of the bars
bar_pos_s1 = rps_ticks - bar_width / 2
bar_pos_s2 = rps_ticks + bar_width / 2

# Set the figure size
plt.figure(figsize=(12, 6))

# Create subplot 1 for dataset_model: RPS vs CPU usage
plt.subplot(1, 2, 1)
plt.bar(bar_pos_s1, df_model['CPU_S1'], width=bar_width, label='Server 1 (3 Cores)')
plt.bar(bar_pos_s2, df_model['CPU_S2'], width=bar_width, label='Server 2 (7 Cores)')
plt.xlabel('Number of requests sent per second')
plt.ylabel('CPU Usage (%)')
plt.yticks(range(0, 110, 10))
plt.title('RPS vs CPU Usage (Round Robin)')
plt.xticks(rps_ticks)
plt.legend()

# Create subplot 2 for dataset_model: RPS vs Total requests processed
plt.subplot(1, 2, 2)
plt.bar(bar_pos_s1, df_model['TotalReq_Server1'],width=bar_width, label='Server 1 (3 Cores)')
plt.bar(bar_pos_s2, df_model['TotalReq_S2'],width=bar_width, label='Server 2 (7 Cores)')
plt.xlabel('Number of requests sent per second')
plt.ylabel('Total Requests Processed')
plt.yticks(range(0, max(df_model['TotalReq_S2']) + 100, 200))
plt.title('RPS vs Total Requests Processed (Round Robin)')
plt.legend()

# Adjust the spacing between subplots
plt.tight_layout()

# Display the plot for dataset_model
plt.show()

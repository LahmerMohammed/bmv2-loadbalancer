import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file
data = pd.read_csv('dataset.csv')

# Extract the columns
rps = data['RPS']

"""
latency = data['RR_Latency']

# Create the line plot
plt.plot(rps, latency, color='red', label='Round Robin')

# Set plot labels and title
plt.xlabel('Request/Second')
plt.ylabel('Latency (ms)')
plt.title('Request/Second vs Latency')

# Add legend
plt.legend()

# Display the plot
plt.show()
"""

cpu_s1 = data['CPU_S1']
cpu_s2 = data['CPU_S2']

# Set the width of the bars
bar_width = 2

# Create the bar plot
plt.bar(rps, cpu_s1, width=bar_width, label='Server 1')
plt.bar(rps + bar_width, cpu_s2, width=bar_width, label='Server 2')

# Set plot labels and title
plt.xlabel('RPS')
plt.ylabel('CPU Usage')
plt.title('RPS vs CPU Usage')

# Add legend
plt.legend()

# Adjust the x-axis tick labels for better visibility
plt.xticks(rotation=45)

# Display the plot
plt.show()
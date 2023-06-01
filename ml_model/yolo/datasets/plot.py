import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data = np.genfromtxt('clean_data.txt', delimiter=' ')

column_names = ['rps', 'cpu_limit','req_rate','req_latency','cpu','cpu0','cpu1','cpu2','cpu3','cpu4','cpu5','cpu6','cpu7','cpu8','cpu9','cpu10','cpu11', 'cpu12', 'cpu13','cpu14', 'cpu15', 'memory_usage']  # Replace with your actual column names
pandas_data = pd.DataFrame(data)
pandas_data.columns = column_names
pandas_data.to_csv('dataset.csv', index=False)



# Read the CSV file into a pandas DataFrame
data = pd.read_csv('dataset.csv')

# Filter the data for cpu_limit >= 4
filtered_data = data[data['cpu_limit'] >= 0]

# Get unique 'rps' values
rps_values = filtered_data['rps'].unique()

# Create a single plot
plt.figure(figsize=(8, 6))

rps_to_include = [1, 5, 10, 20, 30, 40]

# Iterate over 'rps' values and plot each line
for rps in rps_values:
    if rps_to_include.count(rps) == 0:
        continue
    # Filter the data for current 'rps' value
    rps_data = filtered_data[filtered_data['rps'] == rps]
    cpu_limit = rps_data['cpu_limit']
    req_latency = rps_data['req_latency']

    # Plot the line for current 'rps' value
    plt.plot(cpu_limit, req_latency, marker='o', linestyle='-', label=f'rps = {rps}')

# Set x and y-axis labels
plt.xlabel('cpu_limit')
plt.ylabel('req_latency')

# Set the y-axis range and ticks
plt.ylim(30, 100)
plt.yticks(range(30, 100, 2))

# Move the legend to the right and make it smaller
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='small')

# Show the plot
plt.show()
import matplotlib.pyplot as plt
import numpy as np

# Read data from file
with open('stats.txt', 'r') as f:
    lines = f.readlines()

columns = lines[0].strip().split(' ')
    
# Initialize empty lists for each column
data = {column: [] for column in columns}


def plot_num_vCpu_vs_cpu_usage():

    # Extract data values from subsequent entries
    for line in lines[1:]:
        values = line.split()
        for column, value in zip(columns, values):
            data[column].append(float(value))

    # Define color mapping for RPS values
    color_mapping = {1: 'green', 2: 'red', 4: 'blue', 8: 'black'}


    for _rps in set(data["rps"]):
        filtered_data = {
            'cpu_limit': [cpu_limit for rps, cpu_limit in zip(data['rps'], data['cpu_limit']) if rps == _rps],
            'cpu': [cpu for rps, cpu in zip(data['rps'], data['cpu']) if rps == _rps]
        }
        plt.plot(filtered_data['cpu_limit'], filtered_data['cpu'], color=color_mapping[_rps])


    # Adding labels and title
    plt.xlabel('#vCpu')
    plt.ylabel('Cpu usage %')
    plt.title('Cpu usage vs #vCpu')

    plt.ylim(0, 110)
    plt.xlim(1, 4)

    # Create legend based on color mapping
    legend_labels = [f'RPS = {rps}' for rps in color_mapping.keys()]
    legend_colors = list(color_mapping.values())
    plt.legend(legend_labels, loc='best', title='Legend', markerscale=1, frameon=True, facecolor='white', edgecolor='black', bbox_to_anchor=(1.02, 1))


    # Display the plot
    plt.show()


def plot_num_vCpu_vs_req_latency():

    # Extract data values from subsequent entries
    for line in lines[1:]:
        values = line.split()
        for column, value in zip(columns, values):
            data[column].append(float(value))

    # Define color mapping for RPS values
    color_mapping = {1: 'green', 2: 'red', 4: 'blue', 8: 'black'}


    for _rps in set(data["rps"]):
        filtered_data = {
            'cpu_limit': [cpu_limit for rps, cpu_limit in zip(data['rps'], data['cpu_limit']) if rps == _rps],
            'req_latency': [cpu for rps, cpu in zip(data['rps'], data['req_latency']) if rps == _rps]
        }
        plt.plot(filtered_data['cpu_limit'], filtered_data['req_latency'], color=color_mapping[_rps])


    # Adding labels and title
    plt.xlabel('#vCpu')
    plt.ylabel('Request Latency (s) ')
    plt.title('Request Latency vs #vCpu')

    plt.xlim(1, 4)

    # Create legend based on color mapping
    legend_labels = [f'RPS = {rps}' for rps in color_mapping.keys()]
    legend_colors = list(color_mapping.values())
    plt.legend(legend_labels, loc='best', title='Legend', markerscale=1, frameon=True, facecolor='white', edgecolor='black', bbox_to_anchor=(1.02, 1))


    # Display the plot
    plt.show()

def barplot():

    # Sample data
    cpu_cores = [1,2, 3, 4]  # Number of CPU cores
    

    # CPU usage with and without model for different RPS values
    cpu_usage_with_model_rps_1 = [80, 70, 60, 50]
    cpu_usage_without_model_rps_1 = [10, 8, 4, 2]
    cpu_usage_without_model_rps_1 = [cpu_usage_with_model_rps_1[i] - cpu_usage_without_model_rps_1[i] for i in range(len(cpu_cores))]

    cpu_usage_with_model_rps_2 = [90, 80, 70, 60]
    cpu_usage_without_model_rps_2 = [12, 10, 8, 6]
    cpu_usage_without_model_rps_2 = [cpu_usage_with_model_rps_2[i] - cpu_usage_without_model_rps_2[i] for i in range(len(cpu_cores))]

    # Plotting the grouped bar plot
    bar_width = 0.2  # Width of each bar
    index = np.arange(len(cpu_cores))  # X-axis values

    plt.bar(index, cpu_usage_with_model_rps_1, bar_width, color='blue', label='RPS = 1 (With Model)')
    plt.bar(index, cpu_usage_with_model_rps_1, bar_width, color='lightblue', label='RPS = 1 (Without Model)', bottom=cpu_usage_without_model_rps_1)

    plt.bar(index + bar_width, cpu_usage_with_model_rps_2, bar_width, color='orange', label='RPS = 2 (With Model)')
    plt.bar(index + bar_width, cpu_usage_with_model_rps_2, bar_width, color='lightcoral', label='RPS = 2 (Without Model)', bottom=cpu_usage_without_model_rps_2)

    # Adding labels and titles
    plt.xlabel('Number of CPU Cores')
    plt.ylabel('CPU Usage')
    plt.title('CPU Usage with and without Model Execution for Different RPS Values')
    plt.xticks(index + 1.5 * bar_width, cpu_cores)
    plt.legend()

    plt.ylim(1, 110)

    # Display the plot
    plt.show()

import matplotlib.pyplot as plt
import numpy as np

data = []
with open('stats.txt', 'r') as file:
    next(file)  # Skip the header line
    for line in file:
        line = line.strip().split()
        rps = int(line[0])
        cpu_limit = int(line[1])
        req_rate = float(line[2])
        req_latency = float(line[3])
        cpu_total = float(line[4])
        cpu_usage_with_model = float(line[5])
        cpu_usage_without_model = cpu_total - cpu_usage_with_model
        data.append((rps, cpu_limit, req_rate, req_latency, cpu_usage_with_model, cpu_usage_without_model))

# Separate the data by RPS value
rps_values = sorted(list(set(row[0] for row in data)))

print(data)
# Extract CPU cores and CPU usage with and without the model for each RPS value
cpu_cores = np.array(sorted(list(set(row[1] for row in data))))
cpu_usage_with_model = np.array([sum(row[4] for row in data if row[0] == rps) for rps in rps_values])
cpu_usage_without_model = np.array([sum(row[5] for row in data if row[0] == rps) for rps in rps_values])


# Calculate the percentage of CPU usage
total_cpu_usage = cpu_usage_with_model + cpu_usage_without_model
cpu_usage_with_model_percent = cpu_usage_with_model / total_cpu_usage * 100
cpu_usage_without_model_percent = cpu_usage_without_model / total_cpu_usage * 100

# Plotting the bar plot
bar_width = 0.1
rps_offset = [-1.5, -0.5, 0.5, 1.5]  # Offset for each RPS value to position the bars
colors = ['blue', 'orange', 'green', 'red']
labels = ['RPS=1', 'RPS=2', 'RPS=4', 'RPS=8']

for i, offset in enumerate(rps_offset):
    plt.bar(cpu_cores + offset * bar_width, cpu_usage_with_model_percent[i::4], bar_width, color=colors[i], label=labels[i] + ' (with model)', alpha=0.7)
    plt.bar(cpu_cores + offset * bar_width, cpu_usage_without_model_percent[i::4], bar_width, color=colors[i], label=labels[i] + ' (without model)', alpha=0.4, bottom=cpu_usage_with_model_percent[i::4])

# Set y-axis limits
plt.ylim([0, 110])

# Add labels and title
plt.xlabel('Number of CPU Cores')
plt.ylabel('CPU Usage (%)')
plt.title('CPU Usage with and without Model')

# Add legend
plt.legend()

# Display the plot
plt.show()




print(cpu_usage_without_model_percent)
print(cpu_usage_with_model_percent)
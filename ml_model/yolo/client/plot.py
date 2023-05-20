import matplotlib.pyplot as plt
import numpy as np

# Read data from file
with open('stats.txt', 'r') as f:
    lines = f.readlines()

columns = lines[0].strip().split(' ')

# Initialize empty lists for each column
data = {column: [] for column in columns}


def plot_num_vCpu_vs_cpu_usage():

    # Read data from file
    data_file = 'stats.txt'
    data = np.loadtxt(data_file, skiprows=1)  # Read all the data

    # Extract CPU cores and CPU usage for both cases
    cpu_cores = list(set(data[:, 1]))
    cpu_usage = data[:, 4]
    cpu_usage_no_model = data[:, 11]

    # Split the data into two groups: first 4 points and last 4 points
    cpu_usage_first_4 = cpu_usage[:4]
    cpu_usage_no_model_first_4 = cpu_usage_no_model[:4]

    cpu_usage_second_4 = cpu_usage[4:8]
    cpu_usage_no_model_second_4 = cpu_usage_no_model[4:8]

    cpu_usage_third_4 = cpu_usage[8:12]
    cpu_usage_no_model_third_4 = cpu_usage_no_model[8:12]

    cpu_usage_last_4 = cpu_usage[-4:]
    cpu_usage_no_model_last_4 = cpu_usage_no_model[-4:]

    # Calculate the normalized CPU usage
    cpu_usage_normalized_first_4 = np.array(
        cpu_usage_first_4) - np.array(cpu_usage_no_model_first_4)
    cpu_usage_normalized_second_4 = np.array(
        cpu_usage_second_4) - np.array(cpu_usage_no_model_second_4)
    cpu_usage_normalized_third_4 = np.array(
        cpu_usage_third_4) - np.array(cpu_usage_no_model_third_4)
    cpu_usage_normalized_last_4 = np.array(
        cpu_usage_last_4) - np.array(cpu_usage_no_model_last_4)

    # Plotting the bar plot
    bar_width = 0.1
    index = np.arange(len(cpu_cores))

    plt.bar(index + 0.2, cpu_usage_no_model_first_4,
            bar_width, color='blue', alpha=0.3)
    plt.bar(index + 0.2, cpu_usage_normalized_first_4, bar_width, color='blue',
            label='RPS=1', alpha=0.7, bottom=cpu_usage_no_model_first_4)

    plt.bar(index + 0.1, cpu_usage_no_model_second_4,
            bar_width, color='green', alpha=0.3)
    plt.bar(index + 0.1, cpu_usage_normalized_second_4, bar_width, color='green',
            label='RPS=2', alpha=0.7, bottom=cpu_usage_no_model_second_4)

    plt.bar(index, cpu_usage_no_model_third_4,
            bar_width, color='red', alpha=0.3)
    plt.bar(index, cpu_usage_normalized_third_4, bar_width, color='red',
            label='RPS=4', alpha=0.7, bottom=cpu_usage_no_model_third_4)

    plt.bar(index - 0.1, cpu_usage_no_model_last_4,
            bar_width, color='black', alpha=0.3)
    plt.bar(index - 0.1, cpu_usage_normalized_last_4, bar_width, color='black',
            label='RPS=8', alpha=0.7, bottom=cpu_usage_no_model_last_4)

    # Set x-axis tick labels
    plt.xticks(index + bar_width/2, cpu_cores)

    # Add labels and title
    plt.xlabel('Number of CPU Cores')
    plt.ylabel('CPU Usage %')
    plt.title('CPU Usage with and without Model')

    # Add legend
    plt.legend()

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
        plt.plot(filtered_data['cpu_limit'],
                 filtered_data['req_latency'], color=color_mapping[_rps])

    # Adding labels and title
    plt.xlabel('#vCpu')
    plt.ylabel('Request Latency (s) ')
    plt.title('Request Latency vs #vCpu')

    plt.xlim(1, 4)

    # Create legend based on color mapping
    legend_labels = [f'RPS = {rps}' for rps in color_mapping.keys()]
    legend_colors = list(color_mapping.values())
    legend_handles = [plt.Rectangle((0, 0), 0.01, 00.1, color=color) for color in legend_colors]
    plt.legend(legend_handles, legend_labels, loc='best', title='Legend', markerscale=1,
               frameon=True, facecolor='white', edgecolor='black', bbox_to_anchor=(1.02, 1))

    # Display the plot
    plt.show()


plot_num_vCpu_vs_req_latency()

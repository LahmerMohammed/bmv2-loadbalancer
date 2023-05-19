import matplotlib.pyplot as plt

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


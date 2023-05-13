import matplotlib.pyplot as plt

# Read data from file
with open('data.txt', 'r') as f:
    data = f.readlines()
data = [line.strip().split() for line in data]

# Convert data to floats
data = [[float(x) for x in line] for line in data]



# Extract columns
cpu = [line[0] for line in data]
request_rate = [line[1] for line in data]
request_latency = [line[2] for line in data]

# Create a continuous line plot for request rate
fig, ax = plt.subplots()
ax.plot(cpu, request_rate, label='Request Rate', color='green')

# Create a continuous line plot for request latency
ax.plot(cpu, request_latency, label='Request Latency', color='blue')

# Set plot title and axis labels
ax.set_title('CPU vs Request Latency/Rate')
ax.set_xlabel('CPU (millicores)')
ax.set_ylabel('Request Latency (s) / Request Rate (req/s)')

# Add a horizontal line at y=25 to represent 25 requests per second
#ax.axhline(y=25, color='red', linestyle='--', label='Target Request Rate')

# Add legend and grid lines
ax.legend()
ax.grid(True)

# Show plot
plt.show()

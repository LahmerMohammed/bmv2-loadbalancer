import pandas as pd
import numpy as np

column_names = ['rps', 'cpu_limit','req_rate','req_latency','cpu','cpu0','cpu1','cpu2','cpu3','cpu4','cpu5','cpu6','cpu7','cpu8','cpu9','cpu10','cpu11', 'cpu12', 'cpu13','cpu14', 'cpu15', 'memory_usage']  # Replace with your actual column names


def normalize(value):
    return float(value.split('m')[0]) / 1000

new_data = np.genfromtxt('dataset_june_2.txt', delimiter=' ', dtype=str)
func = np.vectorize(normalize)
new_data[:, 1] = func(new_data[:, 1])

new_pandas_data = pd.DataFrame(new_data.astype(float))
new_pandas_data.columns = column_names



data = np.genfromtxt('clean_data.txt', delimiter=' ')
pandas_data = pd.DataFrame(data)
pandas_data.columns = column_names


new_df = pandas_data.append(new_pandas_data)
new_df.columns = column_names

new_df.to_csv('dataset.csv', index=False)


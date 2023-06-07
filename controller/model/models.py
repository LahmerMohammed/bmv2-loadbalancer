from pycaret.regression import setup, compare_models, save_model
import pandas as pd

df = pd.read_csv('dataset.csv')

# Calculate the lower and upper quantiles
lower_quantile = df['req_latency'].quantile(0.05)
upper_quantile = df['req_latency'].quantile(0.95)

# Filter the DataFrame based on the quantiles
filtered_df = df[(df['req_latency'] >= lower_quantile) & (df['req_latency'] <= upper_quantile)]

filtered_df = filtered_df.drop('rps', axis=1)

exp = setup(filtered_df, target='req_latency', normalize=True, normalize_method='minmax')

best_models = compare_models(n_select=5)

for model in best_models:
    save_model(model, model_name=str(model).split('(')[0])

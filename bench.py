import pandas as pd
import time
import numpy as np

# Create a sample DataFrame similar to the one used in the application
data = {
    'id': np.arange(1000),
    'date': pd.date_range(start='1/1/2023', periods=1000),
    'description': ['A short description ' + str(i) for i in range(1000)],
    'amount': np.random.uniform(-1000, 1000, 1000),
    'source': ['Scanned' for _ in range(1000)],
    'file': ['statement.csv' for _ in range(1000)],
    'category': ['Groceries' for _ in range(1000)]
}

df = pd.DataFrame(data)

# Baseline: iterrows
start_time = time.time()
for i, row in df.iterrows():
    date = row['date']
    desc = row['description']
    amt = row['amount']
    src = row['source']
    f = row['file']
    cat = row['category']
    id_val = row['id']
iterrows_time = time.time() - start_time
print(f"iterrows time: {iterrows_time:.4f} seconds")

# Optimized: itertuples
date_idx = df.columns.get_loc('date')
desc_idx = df.columns.get_loc('description')
amt_idx = df.columns.get_loc('amount')
src_idx = df.columns.get_loc('source')
f_idx = df.columns.get_loc('file')
cat_idx = df.columns.get_loc('category')
id_idx = df.columns.get_loc('id')

start_time = time.time()
for i, row in enumerate(df.itertuples(index=False, name=None)):
    date = row[date_idx]
    desc = row[desc_idx]
    amt = row[amt_idx]
    src = row[src_idx]
    f = row[f_idx]
    cat = row[cat_idx]
    id_val = row[id_idx]
itertuples_time = time.time() - start_time
print(f"itertuples time: {itertuples_time:.4f} seconds")

print(f"Speedup: {iterrows_time / itertuples_time:.2f}x")

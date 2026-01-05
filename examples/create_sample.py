"""
Create sample data for testing the synth workflow.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

# Generate sample customer data
df = pd.DataFrame({
    "customer_id": [f"CUST-{i:08d}" for i in range(1, 101)],
    "name": [f"Customer_{i}" for i in range(1, 101)],
    "age": np.random.randint(18, 80, 100),
    "email": [f"customer{i}@example.com" for i in range(1, 101)],
    "salary": np.random.normal(75000, 25000, 100).astype(int),
    "department": np.random.choice(["Engineering", "Sales", "HR", "Marketing"], 100, p=[0.4, 0.3, 0.1, 0.2]),
    "join_date": pd.date_range("2020-01-01", periods=100, freq="D"),
    "is_active": np.random.choice([True, False], 100, p=[0.8, 0.2]),
    "performance_score": np.random.uniform(1, 10, 100),
})

df.to_csv("sample_customers.csv", index=False)
print(f"Created sample_customers.csv with {len(df)} rows")
print(df.head())

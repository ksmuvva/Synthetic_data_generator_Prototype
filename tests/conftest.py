"""
Pytest configuration and shared fixtures.
"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_csv_path(tmp_path):
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "sample.csv"

    np.random.seed(42)
    df = pd.DataFrame({
        "id": range(1, 101),
        "name": [f"Person_{i}" for i in range(1, 101)],
        "age": np.random.randint(18, 80, 100),
        "salary": np.random.normal(75000, 25000, 100),
        "department": np.random.choice(["Engineering", "Sales", "HR", "Marketing"], 100),
        "active": np.random.choice([True, False], 100),
    })

    df.to_csv(csv_path, index=False)
    return csv_path

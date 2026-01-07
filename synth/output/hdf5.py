"""
HDF5 output format for synthetic data.

Provides HDF5 format export capabilities for large datasets.
"""

import pandas as pd
from pathlib import Path


class HDF5Generator:
    """Generate HDF5 format output."""

    def __init__(self, mode: str = "w", complevel: int = 5):
        """
        Initialize generator.

        Args:
            mode: File write mode
            complevel: Compression level (0-9)
        """
        self.mode = mode
        self.complevel = complevel

    def generate(self, df: pd.DataFrame, output_path: str, key: str = "data") -> str:
        """
        Generate HDF5 file.

        Args:
            df: Dataframe to export
            output_path: Output file path
            key: HDF5 dataset key

        Returns:
            Path to generated file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        df.to_hdf(
            output,
            key=key,
            mode=self.mode,
            complevel=self.complevel,
            complib="blosc",
        )

        return str(output)

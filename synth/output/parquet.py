"""
Parquet output format for synthetic data.

Provides Parquet format export capabilities.
"""

import pandas as pd
from pathlib import Path


class ParquetGenerator:
    """Generate Parquet format output."""

    def __init__(self, compression: str = "snappy"):
        """
        Initialize generator.

        Args:
            compression: Compression algorithm (snappy, gzip, brotli)
        """
        self.compression = compression

    def generate(self, df: pd.DataFrame, output_path: str) -> str:
        """
        Generate Parquet file.

        Args:
            df: Dataframe to export
            output_path: Output file path

        Returns:
            Path to generated file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        df.to_parquet(output, compression=self.compression, index=False)

        return str(output)

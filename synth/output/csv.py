"""
CSV output generator.

Simple wrapper around pandas to_csv with additional options.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from synth.output.base import OutputGenerator, GeneratorRegistry
from synth.patterns.schema import Schema


class CSVGenerator(OutputGenerator):
    """Generate CSV output files."""

    def generate(
        self,
        data: pd.DataFrame,
        output_path: Path,
        schema: Optional[Schema] = None,
        **kwargs
    ) -> Path:
        """
        Generate CSV file.

        Args:
            data: DataFrame to write
            output_path: Where to save the CSV
            schema: Optional schema (not used for CSV)
            **kwargs: Additional options (index, encoding, etc.)

        Returns:
            Path to the generated CSV file
        """
        # Default options
        options = {
            "index": False,
            "encoding": "utf-8",
        }
        options.update(kwargs)

        # Ensure output path has .csv extension
        output_path = Path(output_path)
        if output_path.suffix != ".csv":
            output_path = output_path.with_suffix(".csv")

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV
        data.to_csv(output_path, **options)

        return output_path

    def supports_format(self, format_type: str) -> bool:
        """Check if format is supported."""
        return format_type.lower() in ("csv",)


# Register the generator
GeneratorRegistry.register("csv", CSVGenerator)

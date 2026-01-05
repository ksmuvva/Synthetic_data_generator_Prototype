"""
JSON output generator.

Supports both JSON and JSON Lines (JSONL) formats.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

from synth.output.base import OutputGenerator, GeneratorRegistry
from synth.patterns.schema import Schema


class JSONGenerator(OutputGenerator):
    """Generate JSON and JSONL output files."""

    def generate(
        self,
        data: pd.DataFrame,
        output_path: Path,
        schema: Optional[Schema] = None,
        orient: str = "records",
        lines: bool = False,
        **kwargs
    ) -> Path:
        """
        Generate JSON/JSONL file.

        Args:
            data: DataFrame to write
            output_path: Where to save the JSON
            schema: Optional schema
            orient: JSON orientation (records, index, columns, values)
            lines: If True, write JSON Lines format (one record per line)
            **kwargs: Additional options

        Returns:
            Path to the generated JSON file
        """
        # Ensure output path has correct extension
        output_path = Path(output_path)
        if lines and not output_path.suffix == ".jsonl":
            if output_path.suffix != ".jsonl":
                output_path = output_path.with_suffix(".jsonl")
        elif output_path.suffix != ".json":
            output_path = output_path.with_suffix(".json")

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        if lines:
            # JSON Lines format
            data.to_json(output_path, orient="records", lines=True, **kwargs)
        else:
            # Regular JSON
            data.to_json(output_path, orient=orient, indent=2, **kwargs)

        return output_path

    def supports_format(self, format_type: str) -> bool:
        """Check if format is supported."""
        return format_type.lower() in ("json", "jsonl")


# Register the generator
GeneratorRegistry.register("json", JSONGenerator)
GeneratorRegistry.register("jsonl", JSONGenerator)

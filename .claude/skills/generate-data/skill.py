"""
Generate synthetic data using learned patterns.

This skill provides a quick way to generate synthetic data directly from Claude Code
using your existing pattern storage and generation system.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from synth.generation.sampler import StatisticalSampler
from synth.patterns.storage import PatternStorage


def generate_data(pattern_name: str = None, count: int = 10, output_file: str = None, seed: int = None):
    """
    Generate synthetic data from a learned pattern.

    Args:
        pattern_name: Name of the pattern file (with or without .json extension)
        count: Number of records to generate
        output_file: Optional output file path (saves as CSV)
        seed: Optional random seed for reproducibility

    Returns:
        Generated data as a pandas DataFrame
    """
    import pandas as pd

    # Initialize components
    storage = PatternStorage()
    sampler = StatisticalSampler(seed=seed)

    # Find pattern
    if pattern_name is None:
        # List available patterns
        patterns_dir = project_root / "patterns"
        if patterns_dir.exists():
            patterns = list(patterns_dir.glob("*.json"))
            if patterns:
                print(f"Available patterns:")
                for p in patterns:
                    print(f"  - {p.stem}")
                print("\nUsing first available pattern...")
                pattern_name = patterns[0].stem
            else:
                print("No patterns found. Please learn a pattern first using: synth learn <input_file>")
                return None
        else:
            print("No patterns directory found.")
            return None

    # Load pattern
    try:
        pattern_file = f"{pattern_name}.json" if not pattern_name.endswith(".json") else pattern_name
        pattern = storage.load_pattern(pattern_file)
        print(f"✓ Loaded pattern: {pattern.pattern_id}")
    except Exception as e:
        print(f"Failed to load pattern '{pattern_name}': {e}")
        return None

    # Generate data
    print(f"✓ Generating {count:,} records...")
    df = sampler.generate(pattern, count)

    # Output results
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✓ Saved to: {output_path}")
    else:
        print("\nGenerated Data:")
        print(df.to_string(index=False))

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic data from patterns")
    parser.add_argument("pattern", nargs="?", help="Pattern name or file path")
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of records to generate")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-s", "--seed", type=int, help="Random seed for reproducibility")

    args = parser.parse_args()

    generate_data(
        pattern_name=args.pattern,
        count=args.count,
        output_file=args.output,
        seed=args.seed
    )

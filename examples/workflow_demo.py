"""
End-to-end workflow demonstration for Synth.

Self-Reflection Loop:
1. Parse CSV file
2. Extract patterns
3. Generate synthetic data
4. Validate results
"""

import sys
sys.path.insert(0, '..')

import pandas as pd
import numpy as np
from pathlib import Path

# Import synth modules
from synth.input.parser import FileParser
from synth.patterns.schema import SchemaInferrer
from synth.patterns.statistical import UnivariateAnalyzer
from synth.patterns.storage import PatternStorage, create_pattern_from_analysis
from synth.generation.sampler import StatisticalSampler
from synth.validation.engine import ValidationEngine

def main():
    print("=" * 60)
    print("SYNTH - End-to-End Workflow Demo")
    print("=" * 60)

    # Step 1: Parse CSV
    print("\n[Step 1] Parsing source file...")
    parser = FileParser()

    # Look for sample file in parent directory
    sample_path = Path(__file__).parent.parent / "sample_customers.csv"
    df = parser.parse(str(sample_path))
    print(f"  [OK] Parsed {len(df)} rows, {len(df.columns)} columns")

    # Step 2: Extract Schema
    print("\n[Step 2] Inferring schema...")
    schema_inferrer = SchemaInferrer()
    schema = schema_inferrer.infer(df)
    print(f"  [OK] Inferred {len(schema.fields)} fields")

    # Show field types
    print("\n  Fields:")
    for field in schema.fields:
        print(f"    - {field.name}: {field.type.value}")

    # Step 3: Analyze Patterns
    print("\n[Step 3] Analyzing patterns...")
    stat_analyzer = UnivariateAnalyzer()

    numeric_patterns = {}
    categorical_patterns = {}
    string_patterns = {}

    for field in schema.fields:
        if field.type.value in ("integer", "float"):
            series = df[field.name].dropna()
            if len(series) >= 10:
                pattern = stat_analyzer.analyze_numeric(series, field.name)
                numeric_patterns[field.name] = pattern
                print(f"  [OK] {field.name}: {pattern.distribution.dist_type.value}")

        elif field.type.value == "categorical":
            series = df[field.name].dropna()
            if len(series) >= 1:
                pattern = stat_analyzer.analyze_categorical(series, field.name)
                categorical_patterns[field.name] = pattern
                print(f"  [OK] {field.name}: {len(pattern.probabilities)} categories")

        elif field.type.value == "string":
            series = df[field.name].dropna()
            if len(series) >= 1:
                pattern = stat_analyzer.analyze_string(series, field.name)
                string_patterns[field.name] = pattern
                print(f"  [OK] {field.name}: len={pattern.min_length}-{pattern.max_length}")

    # Step 4: Create Pattern
    print("\n[Step 4] Creating pattern...")
    pattern = create_pattern_from_analysis(
        pattern_id="customer_pattern",
        schema=schema,
        numeric_patterns=numeric_patterns,
        categorical_patterns=categorical_patterns,
        string_patterns=string_patterns,
        source_files=["sample_customers.csv"],
    )
    print(f"  [OK] Pattern created with {pattern.row_count} source rows")

    # Step 5: Save Pattern
    print("\n[Step 5] Saving pattern...")
    storage = PatternStorage()

    # Save to examples directory
    output_dir = Path(__file__).parent
    output_path = output_dir / "customer_pattern.json"
    output_path = storage.save_pattern(pattern, str(output_path))
    print(f"  [OK] Pattern saved to: {output_path}")

    # Step 6: Generate Synthetic Data
    print("\n[Step 6] Generating synthetic data...")
    sampler = StatisticalSampler(seed=42)
    synthetic_df = sampler.generate(pattern, 500)
    print(f"  [OK] Generated {len(synthetic_df)} synthetic records")

    # Step 7: Validate
    print("\n[Step 7] Validating synthetic data...")
    validator = ValidationEngine()
    result = validator.validate(synthetic_df, df)

    print(f"\n  Quality Score: {result.quality_score:.2f}")
    print(f"  Status: {result.overall_status.value.upper()}")
    print(f"  Schema Score: {result.schema_score:.2f}")
    print(f"  Statistical Score: {result.statistical_score:.2f}")
    print(f"  Constraint Score: {result.constraint_score:.2f}")

    # Show test results
    print(f"\n  Test Results:")
    for test in result.test_results[:5]:
        status_symbol = "[OK]" if test.status.value == "pass" else "[!]" if test.status.value == "warning" else "[X]"
        print(f"    {status_symbol} {test.test_name}: {test.message}")

    # Step 8: Save Output
    print("\n[Step 8] Saving synthetic data...")
    synthetic_path = output_dir / "synthetic_customers.csv"
    synthetic_df.to_csv(synthetic_path, index=False)
    print(f"  [OK] Saved to: {synthetic_path}")

    # Show sample
    print(f"\n  Sample Data (first 3 rows):")
    print(synthetic_df.head(3).to_string(index=False))

    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - customer_pattern.json (learned pattern)")
    print("  - synthetic_customers.csv (synthetic data)")
    print("\nNext steps:")
    print("  - Adjust pattern parameters if needed")
    print("  - Generate more data: python -c \"...\"")
    print("  - Run validation report")

if __name__ == "__main__":
    main()

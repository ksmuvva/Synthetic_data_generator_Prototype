# Synthetic Data Generator AI Agent

> Build the world's most accurate and versatile synthetic data generation AI agent that understands complex data patterns from multiple sources and generates statistically valid, privacy-safe synthetic datasets through an intuitive CLI interface.

## Vision

A CLI-based synthetic data generator that:
- **Pattern Intelligence**: Automatically extracts statistical, structural, and semantic patterns from any data source
- **Multi-Modal Mastery**: Processes text prompts, CSVs, Excel, PDFs, and documents with equal proficiency
- **Deterministic Validation**: Built-in validation framework using statistical metrics
- **Production-Ready**: Generates data that passes rigorous quality gates

## Quick Start

```bash
# Install the package
pip install synth-agent

# Initialize a new project
synth init my-project --type tabular

# Learn patterns from existing data
synth learn --source customers.csv --name customer_pattern

# Generate synthetic data
synth generate --pattern customer_pattern --count 10000 --output synthetic_customers.csv

# Validate the generated data
synth validate --synthetic synthetic_customers.csv --reference customers.csv
```

## Core Commands

| Command | Description |
|---------|-------------|
| `synth init` | Initialize a new project |
| `synth learn` | Extract patterns from data sources |
| `synth generate` | Generate synthetic data |
| `synth validate` | Validate generated data quality |
| `synth inspect` | Inspect learned patterns |
| `synth export/import` | Export/import patterns |

## Key Features

### 1. Multi-Format Input Processing
- CSV, Excel, JSON, PDF, DOCX, SQL dumps
- Natural language prompts
- Hybrid (file + prompt) inputs

### 2. Intelligent Pattern Learning
- Statistical distribution fitting
- Correlation and dependency discovery
- Semantic entity recognition
- Business rule extraction

### 3. Advanced Generation Strategies
- Statistical sampling
- Copula-based multivariate generation
- Constraint satisfaction
- LLM-guided generation (Claude API)

### 4. Comprehensive Validation
- Statistical tests (KS, Chi-Square, Wasserstein)
- Schema and constraint validation
- Semantic validity checks
- ML utility assessment

## Project Status

**Phase**: MVP Development (Week 1-4)

- [x] Requirements Document
- [ ] Project Structure
- [ ] CLI Framework
- [ ] CSV Parser & Schema Inference
- [ ] Statistical Pattern Learning
- [ ] Basic Generation Engine
- [ ] Validation Framework

## Installation

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ksmuvva/Synthetic_data_generator_Prototype.git
cd Synthetic_data_generator_Prototype

# Install with Poetry (recommended)
poetry install

# Or with pip
pip install -e .
```

## Documentation

- [Requirements Document](REQUIREMENTS.md) - Comprehensive system requirements
- [User Guide](docs/user_guide.md) - How to use the tool
- [API Reference](docs/api_reference.md) - Programmatic access
- [Examples](examples/) - Example workflows

## Architecture

```
CLI Interface
    ↓
Input Handler → Pattern Learner → Generation Engine → Validation Engine
    ↓                ↓                    ↓                    ↓
  Files/Prompts   Statistical/     Generation         Validation Reports
                 Semantic        Strategies          & Metrics
```

## Contributing

This project is currently in active development. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built with:
- Python 3.11+
- Typer + Rich for CLI
- Pandas/Polars for data processing
- SciPy for statistical analysis
- Anthropic Claude API for LLM-guided generation

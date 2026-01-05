<div align="center">

  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green?logo=github" alt="License"/>
  <img src="https://img.shields.io/badge/Tests-79%20Passing-success?logo=pytest" alt="Tests"/>

  # Synth

  ### AI-Powered Synthetic Data Generator

  Generate realistic synthetic data through a simple chat interface.

  [Quick Start](#-quick-start) • [Features](#-features) • [Examples](#-examples) • [Docs](#-documentation)

</div>

---

## Summary

**Synth** is a command-line tool that generates synthetic data using AI. Just describe what you need in plain English, and it creates statistically valid datasets.

```bash
# One command to start
python -m synth agent chat

# Then just type:
> Create 100 customer records with name, email, and age

# Done! 🎉
```

## Quick Start

### 1. Install

```bash
git clone https://github.com/ksmuvva/Synthetic_data_generator_Prototype.git
cd Synthetic_data_generator_Prototype
pip install -e .
```

### 2. Get an API Key

Choose a provider:

| Provider | Best For | Get Key |
|----------|----------|---------|
| Claude | Best reasoning | [console.anthropic.com](https://console.anthropic.com/) |
| GPT-4 | Fast response | [platform.openai.com](https://platform.openai.com/api-keys) |
| Gemini | Large context | [makersuite.google.com](https://makersuite.google.com/app/apikey) |

### 3. Run

```bash
python -m synth agent chat
```

The setup wizard will guide you through:
1. Select provider (press Enter for Claude)
2. Choose model (press Enter for recommended)
3. Enter API key
4. Describe your data
5. Get results!

---

## Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Chat** | Natural language interface - just describe what you need |
| 🎯 **Multi-Provider** | Claude, OpenAI, Gemini support |
| 📊 **Smart Patterns** | Learns statistical distributions from your data |
| 📄 **Multi-Format** | CSV, Excel, PDF, Word, JSON |
| ✅ **Validation** | Statistical quality checks built-in |
| ⚡ **Progress Tracking** | Real-time feedback with time estimates |

---

## Examples

### Generate Customer Records

```bash
$ python -m synth agent chat
> Create 50 customers with name, email, age

AI: Got it! Generating 50 customer records...
✓ Building schema...
✓ Generating 50 records... ████████████████████ 100% (50/50)
✓ Saved to: customers_20240105.csv
```

### Financial Transactions

```bash
> Generate 1000 transactions, $10-$5000, dates in 2024

AI: Perfect! Creating 1000 financial transactions...
✓ Saved to: transactions_20240105.csv
```

### Learn From Existing Data

```bash
# Learn from your data
synth learn --source customers.csv --name my_pattern

# Generate more like it
synth generate --pattern my_pattern --count 10000 --output more_customers.csv

# Validate quality
synth validate --synthetic more_customers.csv --reference customers.csv
```

---

## Commands

| Command | Description |
|---------|-------------|
| `synth agent chat` | Start AI chat mode (recommended) |
| `synth learn` | Learn patterns from existing data |
| `synth generate` | Generate synthetic data |
| `synth validate` | Validate data quality |
| `synth inspect` | View learned patterns |

---

## CLI Options

```bash
# Skip setup wizard (use env vars)
python -m synth agent chat --skip-setup

# Specify provider
python -m synth agent chat -p openai

# Specify model
python -m synth agent chat -m gpt-4o

# Environment variables
export ANTHROPIC_API_KEY=sk-ant-xxx
export OPENAI_API_KEY=sk-xxx
export GOOGLE_API_KEY=xxx
```

---

## Architecture

```
User Input (Chat)
       ↓
   AI Agent (LLM)
       ↓
  Schema Builder
       ↓
  Data Generator
       ↓
  Multi-Format Output
```

---

## Development

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest --cov=synth tests/

# Run demo
python examples/ux_improvements_demo.py
```

**Status:** 79 tests passing ✅

---

## Project Structure

```
synth/
├── agent/          # AI Agent (chat, wizard, LLM providers)
├── cli/            # Command-line interface
├── patterns/       # Pattern learning & storage
├── generation/     # Data generation engine
├── validation/     # Statistical validation
├── input/          # File parsers (CSV, Excel, PDF, etc.)
└── output/         # Output generators (CSV, Excel, PDF, etc.)
```

---

## Contributing

Contributions welcome! Areas to help:

- Additional LLM providers
- New data templates
- More validation metrics
- Documentation improvements

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Links

- [Documentation](docs/)
- [Examples](examples/)
- [Issues](https://github.com/ksmuvva/Synthetic_data_generator_Prototype/issues)

---

<div align="center">

  Made with ❤️ | [GitHub](https://github.com/ksmuvva/Synthetic_data_generator_Prototype)

</div>

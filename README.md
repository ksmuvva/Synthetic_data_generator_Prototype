<div align="center">

  # Synth - AI-Powered Synthetic Data Generator

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Tests](https://img.shields.io/badge/Tests-79%20Passing-success.svg)](tests/)

  **The world's most sophisticated AI-powered synthetic data generator**

  Generate statistically valid, privacy-safe synthetic datasets through an intuitive conversational AI interface.

  [Features](#-key-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples)

</div>

---

## Overview

**Synth** is a production-ready synthetic data generator that combines:

- **LLM-Powered AI Agent** - Interactive chat interface for natural data generation
- **Multi-Provider Support** - Claude, OpenAI GPT-4, Google Gemini
- **Statistical Intelligence** - Advanced pattern learning and distribution fitting
- **Multi-Format I/O** - CSV, Excel, PDF, Word, JSON
- **Validation Framework** - Statistical quality assurance with KS, Chi-Square tests

---

## Key Features

### 🤖 AI Agent Mode (New!)

```
                    The most sophisticated way to
                    generate synthetic data

    Interactive Setup Wizard → AI Conversation → Instant Results
```

- **Natural Language Interface** - Just describe what you need
- **Intelligent Clarification** - AI asks the right questions
- **Visual Progress Tracking** - Real-time feedback with time estimates
- **Multi-Provider LLM Support**:
  - Claude (Anthropic) - Extended thinking, 200K context
  - GPT-4 (OpenAI) - Fast response, widely adopted
  - Gemini (Google) - 1M context window, multimodal

### 📊 Pattern Learning

- **Statistical Distribution Fitting** - Normal, LogNormal, Exponential, Uniform
- **Correlation Discovery** - Multi-variate dependency detection
- **Schema Inference** - Automatic field type detection
- **Business Rule Extraction** - Constraints and validations

### 🎯 Multi-Format Support

| Format | Input | Output |
|--------|-------|--------|
| CSV | ✅ | ✅ |
| Excel | ✅ | ✅ |
| JSON | ✅ | ✅ |
| PDF | ✅ | ✅ |
| Word | ✅ | ✅ |

### ✅ Validation Framework

- **Statistical Tests** - Kolmogorov-Smirnov, Chi-Square, Wasserstein
- **Schema Validation** - Column types, constraints, uniqueness
- **ML Utility** - Feature importance preservation
- **Privacy Metrics** - k-anonymity, l-diversity assessment

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ksmuvva/Synthetic_data_generator_Prototype.git
cd Synthetic_data_generator_Prototype

# Install with Poetry (recommended)
poetry install

# Or with pip
pip install -e .
```

### Option 1: AI Agent Mode (Recommended for Beginners)

The interactive setup wizard guides you through everything:

```bash
python -m synth agent chat
```

**What happens:**
1. Select your AI provider (Claude, OpenAI, or Gemini)
2. Choose your model (recommended models marked)
3. Enter your API key
4. Describe your data needs in plain English
5. AI clarifies requirements and generates data

**Example conversation:**

```
You: Create 100 financial transactions

AI: I understand you want 100 financial transactions. Let me clarify:

1. What currency should be used?
> USD

2. What date range should the transactions cover?
> 2024-01-01 to 2024-12-31

3. Any specific transaction categories?
> Retail, restaurants, gas stations

✓ Generating 100 records...
✓ Saved to: transactions_20240105.csv
```

### Option 2: Traditional CLI Mode

```bash
# Learn patterns from existing data
synth learn --source customers.csv --name customer_pattern

# Generate synthetic data
synth generate --pattern customer_pattern --count 10000 --output synthetic_customers.csv

# Validate the generated data
synth validate --synthetic synthetic_customers.csv --reference customers.csv
```

### Setting API Keys

**Option A: Environment Variable (Recommended)**

```bash
# Windows Command Prompt
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Linux/Mac
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Option B: Skip Setup Mode**

```bash
python -m synth agent chat --skip-setup --provider claude
```

---

## Documentation

| Documentation | Description |
|--------------|-------------|
| [User Guide](docs/user_guide.md) | Comprehensive usage guide |
| [API Reference](docs/api_reference.md) | Programmatic access |
| [Examples](examples/) | Example workflows |
| [Requirements](REQUIREMENTS.md) | System requirements |

---

## CLI Commands

### AI Agent Commands

| Command | Description |
|---------|-------------|
| `synth agent chat` | Start interactive AI agent with setup wizard |
| `synth agent chat --skip-setup` | Skip wizard, use environment variables |
| `synth agent chat -p openai` | Specify provider (claude/openai/gemini) |
| `synth agent chat -m gpt-4o` | Specify model |

### Core Commands

| Command | Description |
|---------|-------------|
| `synth init` | Initialize a new project |
| `synth learn` | Extract patterns from data sources |
| `synth generate` | Generate synthetic data |
| `synth validate` | Validate generated data quality |
| `synth inspect` | Inspect learned patterns |
| `synth export` | Export patterns to file |
| `synth import` | Import patterns from file |

---

## Examples

### Example 1: Generate Customer Records

```bash
python -m synth agent chat
```

```
> Create 50 customer records with name, email, and age

AI: I'll create 50 customer records. Confirming:
  - Fields: name, email, age
  - Count: 50 records
  - Age range: 18-100 (reasonable for customers)

Generate now? [Y/n]: Y

✓ Building schema...
✓ Creating generation pattern...
✓ Generating 50 records...
██████████████████████████████████████ 100% (50/50) 0:00:02
✓ Saved to: customers_20240105.csv
```

### Example 2: Financial Transactions

```bash
python -m synth agent chat
```

```
> Generate 1000 financial transactions

AI: I need a few details:
1. Transaction type? [financial/payroll/other]
> financial

2. Amount range?
> $10 to $5000

3. Date range?
> 2024-01-01 to 2024-12-31

✓ Generating 1000 records...
✓ Saved to: financial_transactions_20240105.csv
```

### Example 3: Using Existing Data as Template

```bash
# Learn from existing data
synth learn --source original_customers.csv --name customer_pattern

# Generate 10x more data
synth generate --pattern customer_pattern --count 100000 --output scaled_customers.csv

# Validate quality
synth validate --synthetic scaled_customers.csv --reference original_customers.csv
```

### Example 4: Multi-Format Output

```bash
python -m synth agent chat
```

```
> Create 500 user profiles and save as PDF

AI: Generating 500 user profiles...
✓ Saved to: user_profiles_20240105.pdf

> Now save the same data as Excel
✓ Saved to: user_profiles_20240105.xlsx
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ AI Agent     │  │ Traditional   │  │ Validation           │  │
│  │ Chat Mode    │  │ CLI Commands  │  │ Engine               │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘  │
└─────────┼──────────────────┼───────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Processing Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ LLM          │  │ Pattern      │  │ Generation           │  │
│  │ Providers    │  │ Learner      │  │ Engine               │  │
│  │              │  │              │  │                      │  │
│  │ • Claude     │  │ • Schema     │  │ • Statistical        │  │
│  │ • GPT-4      │  │   Inference  │  │   Sampling           │  │
│  │ • Gemini     │  │ • Dist       │  │ • Distribution       │  │
│  │              │  │   Fitting    │  │   Fitting            │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Layer                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Input        │  │ Pattern      │  │ Output               │  │
│  │ Parsers      │  │ Storage      │  │ Generators          │  │
│  │              │  │              │  │                      │  │
│  │ • CSV        │  │ • JSON       │  │ • CSV                │  │
│  │ • Excel      │  │ • Pickle     │  │ • Excel              │  │
│  │ • PDF        │  │              │  │ • PDF                │  │
│  │ • Word       │  │              │  │ • Word               │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## UX Features

Our AI Agent includes industry-leading user experience features:

| Feature | Description |
|---------|-------------|
| **Loading Spinners** | Visual feedback during API calls |
| **Progress Tracking** | Real-time "Generating X/Y..." with percentage |
| **Time Estimates** | "~50 seconds remaining" countdown |
| **Recommended Badges** | Default models marked for beginners |
| **Keyboard Shortcuts** | Ctrl+C hints throughout |
| **Edit Option** | Go back and change selections anytime |

**UX Score**: 8.0/10 (Significant improvements! Ready for production)

---

## Getting API Keys

### Claude (Anthropic) - Recommended

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new key
5. Copy the key (starts with `sk-ant-`)

### OpenAI GPT-4

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click **+ Create new secret key**
4. Copy the key (starts with `sk-`)

### Google Gemini

1. Go to [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign up or log in
3. Create a new API key
4. Copy the key

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=synth tests/

# Run specific test file
pytest tests/test_llm_agent.py -v
```

**Current Test Status**: 79 tests passing ✅

### Project Structure

```
synth/
├── agent/              # AI Agent module
│   ├── llm/           # LLM providers (Claude, OpenAI, Gemini)
│   │   ├── __init__.py
│   │   ├── parser.py   # Natural language parser
│   │   ├── session.py  # Interactive agent session
│   │   └── wizard.py   # Setup wizard
│   ├── templates/     # Pre-built schema templates
│   │   ├── financial.py
│   │   ├── ecommerce.py
│   │   └── user_profile.py
│   └── state.py       # Conversation state management
├── cli/               # CLI commands
│   └── agent.py       # AI agent command
├── patterns/          # Pattern learning
│   ├── schema.py      # Schema inference
│   └── storage.py     # Pattern persistence
├── generation/        # Data generation
│   └── sampler.py     # Statistical sampling
├── validation/        # Validation framework
│   └── engine.py      # Statistical tests
├── input/             # Input parsers
│   └── parser.py      # Multi-format parser
└── output/            # Output generators
    ├── csv.py
    ├── excel.py
    ├── pdf.py
    ├── word.py
    └── json.py
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution

- **Additional LLM Providers** - Add support for more providers
- **New Templates** - Create pre-built schemas for common use cases
- **Validation Metrics** - Add more statistical tests
- **Documentation** - Improve examples and guides
- **Performance** - Optimize generation speed

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with:

- **[Python](https://www.python.org/)** 3.11+ - Core language
- **[Typer](https://typer.tiangolo.com/)** - CLI framework
- **[Rich](https://rich.readthedocs.io/)** - Terminal formatting
- **[Pandas](https://pandas.pydata.org/)** - Data processing
- **[SciPy](https://www.scipy.org/)** - Statistical analysis
- **[Anthropic Claude](https://www.anthropic.com/)** - LLM API
- **[OpenAI](https://openai.com/)** - GPT-4 API
- **[Google Gemini](https://ai.google.dev/)** - Gemini API

---

<div align="center">

  **[⬆ Back to Top](#-synth---ai-powered-synthetic-data-generator)**

  Made with ❤️ by the Synth team

  **[GitHub](https://github.com/ksmuvva/Synthetic_data_generator_Prototype)** •
  **[Issues](https://github.com/ksmuvva/Synthetic_data_generator_Prototype/issues)** •
  **[Documentation](docs/)**

</div>

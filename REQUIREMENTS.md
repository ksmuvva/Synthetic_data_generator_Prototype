# Synthetic Data Generator - Requirements Document

## 1. Executive Summary

### Vision Statement
Build the world's most accurate and versatile synthetic data generation AI agent that understands complex data patterns from multiple sources and generates statistically valid, privacy-safe synthetic datasets through an intuitive CLI interface.

### Core Value Proposition
- **Pattern Intelligence**: Automatically extracts and understands statistical, structural, and semantic patterns from any data source
- **Multi-Modal Mastery**: Processes text prompts, CSVs, Excel, PDFs, and documents with equal proficiency
- **Deterministic Validation**: Built-in validation framework using statistical metrics, not probabilistic LLM judges
- **Production-Ready**: Generates data that passes rigorous quality gates for immediate use in ML pipelines

### Key Differentiators
- Hybrid Input System: Combines natural language instructions with file-based pattern learning
- Explainable Generation: Every synthetic record can be traced back to learned patterns
- Validation-First Architecture: Metrics computed in real-time during generation

---

## 2. Functional Requirements

### FR1: CLI Interface & Commands

**Core Commands:**
```bash
synth init [project-name] --type [tabular|text|mixed]
synth learn --source [file-path|prompt] --name [pattern-name]
synth generate --pattern [pattern-name] --count [n] --output [file-path]
synth validate --synthetic [file-path] --reference [file-path] --metrics [all|distribution|schema|semantic]
synth inspect --pattern [pattern-name] --detail [summary|full|stats]
synth export/import patterns
synth interactive --pattern [pattern-name]
synth batch --config [yaml-file]
```

### FR2: Multi-Format Input Processing

| Format | Capabilities | Priority |
|--------|--------------|----------|
| CSV | Column types, distributions, correlations, null patterns | P0 |
| Excel | Multi-sheet analysis, formulas, validation rules | P0 |
| JSON | Schema inference, nested structures, array patterns | P0 |
| PDF | Table extraction, text patterns | P1 |
| SQL Dumps | Schema, constraints, data distributions | P2 |

**Prompt-Based Input Types:**
- Structured description: "Generate customer records with ages 25-65..."
- Example-based: "Here are 5 examples. Generate 1000 more..."
- Constraint-based: "Create transaction data where amount > 0..."
- Hybrid: File + prompt combinations

### FR3: Pattern Extraction Engine

**Statistical Pattern Learning:**
- **Univariate**: Distribution fitting (normal, lognormal, exponential, etc.)
- **Multivariate**: Correlations (Pearson, Spearman), conditional distributions
- **Structural**: Primary keys, foreign keys, business rules

**Semantic Pattern Learning:**
- Entity recognition (names, organizations, locations)
- Domain-specific patterns (financial, healthcare, ecommerce)

### FR4: Synthetic Data Generation

**Generation Strategies:**
1. Statistical Sampling (Fast, independent columns)
2. Copula-based (Preserves correlations)
3. Constraint Satisfaction (Business rules, referential integrity)
4. LLM-guided (Semantic coherence via Claude API)
5. Hybrid (Combination of above)

**Generation Modes:**
- Exact count, match source size, scaled (2x, 10x, 100x)
- Streaming for large datasets
- Conditional generation
- Augmentation (add to existing)

### FR5: Validation & Quality Metrics

**Statistical Validation:**
- Kolmogorov-Smirnov test, Chi-Square test
- Wasserstein distance, moment matching
- Correlation preservation (matrix distance)

**Schema Validation:**
- Type conformance, constraint satisfaction
- Referential integrity, business rules

**Utility Validation:**
- ML model performance comparison
- Feature importance similarity
- Query result matching

### FR6: Output Management

**Export Formats:** CSV, Excel, JSON, Parquet, SQL inserts
**Features:** Streaming, compression, multi-format export, metadata generation

---

## 3. Non-Functional Requirements

### Performance Targets
- Pattern learning: < 10s (small), < 2min (medium), < 15min (large)
- Generation speed: > 10K records/sec (simple), > 1K/sec (complex)
- Validation: < 5s (10K records, basic), < 30s (full suite)

### Scalability
- Max input file size: 10 GB
- Max synthetic generation: 100M records
- Max columns: 1000

### Security & Privacy
- Differential privacy (ε=1.0)
- K-anonymity enforcement
- PII detection and anonymization

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                          │
└────────────────────┬────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    ▼                ▼                ▼
Input Handler  Pattern Learner  Generation Engine
    │                │                │
    └────────────────┼────────────────┤
                     ▼                ▼
              Validation Engine  Output Manager
                     │                │
                     ▼                ▼
              Validation Report  Synthetic Data
```

---

## 5. Technical Stack

**Core:** Python 3.11+, Typer, Rich
**Data Processing:** Pandas, Polars, PyArrow
**Statistical:** NumPy, SciPy, Scikit-learn
**Output:** Faker, Mimesis
**Config:** Pydantic, PyYAML

---

## 6. Implementation Roadmap

### Phase 1: MVP (Weeks 1-4)
- Week 1: Project setup, CLI framework
- Week 2: CSV parser, univariate analysis, pattern storage
- Week 3: Statistical sampling generator, basic constraints
- Week 4: Schema validation, basic statistical tests

### Phase 2: Enhanced Features (Weeks 5-8)
- Week 5: Multi-format support (Excel, JSON, PDF)
- Week 6: Correlations, copulas, functional dependencies
- Week 7: Prompt-based generation, Claude API integration
- Week 8: Full validation suite, HTML reports

### Phase 3: Production Readiness (Weeks 9-12)
- Week 9: Privacy controls (differential privacy, k-anonymity)
- Week 10: Performance optimization, streaming, parallel processing
- Week 11: Multi-table/relational data support
- Week 12: Documentation, examples, polish

---

## 7. Validation Thresholds

| Category | Metric | Threshold |
|----------|--------|-----------|
| Schema | Type conformance | 100% |
| Schema | Uniqueness | 100% |
| Statistical | KS test p-value | > 0.05 |
| Statistical | Correlation MAE | < 0.1 |
| Semantic | Entity plausibility | > 95% |
| Utility | ML performance ratio | > 0.90 |
| Overall | Quality score | > 0.85 |

---

## 8. Project Status

**Current Phase:** MVP Development (Week 1)

- [x] Requirements document
- [x] Project structure
- [x] Configuration files
- [ ] CLI framework implementation
- [ ] CSV parser
- [ ] Pattern learning engine
- [ ] Generation engine
- [ ] Validation framework

---

## Document Version

- Version: 1.0
- Last Updated: 2026-01-05
- Author: ksmuvva

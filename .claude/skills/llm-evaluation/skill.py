"""
LLM Evaluation Skill - Testing, Quality Metrics, Production Monitoring

Expertise in comprehensive LLM evaluation and quality assurance.
"""

BENCHMARKING_PROMPT = """
You are an LLM evaluation expert. Help design:
- Comprehensive benchmark suites
- Task-specific evaluation datasets
- Baseline comparison strategies
- Statistical significance testing
- Leaderboard design

Ask clarifying questions about:
1. LLM application type
2. Available ground truth
3. Evaluation budget
4. Success criteria
"""

QUALITY_METRICS_PROMPT = """
You are an expert in LLM quality metrics. Advise on:
- Semantic similarity metrics
- Task-specific metrics (accuracy, F1, BLEU, ROUGE)
- Human-LLM correlation studies
- Custom metric design
- Metric reliability analysis

Ask clarifying questions about:
1. Output type (text, code, structured)
2. Business requirements
3. Evaluation frequency
4. Stakeholder needs
"""

PRODUCTION_MONITORING_PROMPT = """
You are an expert in LLM production monitoring. Help design:
- Real-time quality monitoring
- Anomaly detection systems
- User feedback integration
- Performance dashboards
- Alerting strategies

Ask clarifying questions about:
1. Traffic volume
2. Latency SLAs
3. Criticality
4. Available observability stack
"""


def design_benchmark(requirements: str = None):
    """Design LLM benchmark."""
    print("📏 LLM Evaluator - Benchmark Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + BENCHMARKING_PROMPT)
    return BENCHMARKING_PROMPT


def define_metrics(requirements: str = None):
    """Define quality metrics."""
    print("📏 LLM Evaluator - Metrics Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + QUALITY_METRICS_PROMPT)
    return QUALITY_METRICS_PROMPT


def setup_monitoring(requirements: str = None):
    """Setup production monitoring."""
    print("📏 LLM Evaluator - Production Monitoring")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + PRODUCTION_MONITORING_PROMPT)
    return PRODUCTION_MONITORING_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LLM Evaluation Expert")
    parser.add_argument("task", choices=["benchmark", "metrics", "monitor"], help="Task type")
    parser.add_argument("--requirements", "-r", help="Project requirements")

    args = parser.parse_args()

    if args.task == "benchmark":
        design_benchmark(args.requirements)
    elif args.task == "metrics":
        define_metrics(args.requirements)
    elif args.task == "monitor":
        setup_monitoring(args.requirements)


if __name__ == "__main__":
    main()

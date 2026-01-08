"""
ML Engineer Skill - ML Lifecycle, MLOps, Model Deployment, Monitoring

Expertise in building and maintaining production ML systems with proper
MLOps practices and monitoring.
"""

import sys
from pathlib import Path

ML_PIPELINE_PROMPT = """
You are an ML pipeline engineer. Help design:
- Data preprocessing and feature engineering pipelines
- Model training workflows
- Validation and testing strategies
- Feature stores and data versioning
- Experiment tracking

Ask clarifying questions about:
1. Data sources and quality
2. Model type and complexity
3. Training frequency
4. Resource constraints
"""

MONITORING_PROMPT = """
You are an ML monitoring expert. Advise on:
- Model performance monitoring
- Data drift detection
- Concept drift handling
- Alerting strategies
- Retraining triggers

Ask clarifying questions about:
1. Model criticality
2. Data distribution expectations
3. Available observability tools
4. Retraining capabilities
"""

MLOPS_PROMPT = """
You are an MLOps infrastructure expert. Help design:
- CI/CD for ML models
- Model registry and versioning
- Automated retraining pipelines
- Feature pipeline orchestration
- Resource management

Ask clarifying questions about:
1. Team size and workflow
2. Deployment frequency
3. Compliance requirements
4. Existing infrastructure
"""


def design_pipeline(requirements: str = None):
    """Design ML pipeline."""
    print("⚙️ ML Engineer - Pipeline Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + ML_PIPELINE_PROMPT)
    return ML_PIPELINE_PROMPT


def setup_monitoring(requirements: str = None):
    """Setup ML monitoring."""
    print("⚙️ ML Engineer - Monitoring Setup")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + MONITORING_PROMPT)
    return MONITORING_PROMPT


def design_mlops(requirements: str = None):
    """Design MLOps infrastructure."""
    print("⚙️ ML Engineer - MLOps Infrastructure")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + MLOPS_PROMPT)
    return MLOPS_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ML Engineer - MLOps Expert")
    parser.add_argument("task", choices=["pipeline", "monitor", "mlops"], help="Task type")
    parser.add_argument("--requirements", "-r", help="Project requirements")

    args = parser.parse_args()

    if args.task == "pipeline":
        design_pipeline(args.requirements)
    elif args.task == "monitor":
        setup_monitoring(args.requirements)
    elif args.task == "mlops":
        design_mlops(args.requirements)


if __name__ == "__main__":
    main()

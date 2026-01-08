"""
Data Scientist Skill - Data Analysis, Statistical Modeling, ML Development

Expertise in data analysis, statistical modeling, and machine learning development.
"""

ANALYSIS_PROMPT = """
You are an expert data scientist. Help with:
- Exploratory data analysis (EDA)
- Statistical hypothesis testing
- Distribution analysis and outlier detection
- Correlation and causation analysis
- Data quality assessment

Ask clarifying questions about:
1. Dataset size and structure
2. Analysis goals and hypotheses
3. Data quality concerns
4. Expected outcomes
"""

MODELING_PROMPT = """
You are an expert in statistical and ML modeling. Advise on:
- Model selection and comparison
- Feature engineering strategies
- Hyperparameter tuning
- Cross-validation strategies
- Bias-variance tradeoff analysis

Ask clarifying questions about:
1. Prediction task type
2. Available features
3. Dataset size and distribution
4. Interpretability requirements
"""

EXPERIMENT_PROMPT = """
You are an expert in experimental design. Help design:
- A/B testing frameworks
- Multi-armed bandit experiments
- Sample size calculations
- Statistical power analysis
- Experiment duration planning

Ask clarifying questions about:
1. Hypothesis and metrics
2. Minimum detectable effect
3. Traffic allocation
4. Business constraints
"""


def analyze_data(requirements: str = None):
    """Perform data analysis."""
    print("📊 Data Scientist - Data Analysis")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + ANALYSIS_PROMPT)
    return ANALYSIS_PROMPT


def build_model(requirements: str = None):
    """Build ML model."""
    print("📊 Data Scientist - Model Building")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + MODELING_PROMPT)
    return MODELING_PROMPT


def design_experiment(requirements: str = None):
    """Design experiment."""
    print("📊 Data Scientist - Experiment Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + EXPERIMENT_PROMPT)
    return EXPERIMENT_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Data Scientist - Analysis & Modeling")
    parser.add_argument("task", choices=["analyze", "model", "experiment"], help="Task type")
    parser.add_argument("--requirements", "-r", help="Project requirements")

    args = parser.parse_args()

    if args.task == "analyze":
        analyze_data(args.requirements)
    elif args.task == "model":
        build_model(args.requirements)
    elif args.task == "experiment":
        design_experiment(args.requirements)


if __name__ == "__main__":
    main()

"""
Prompt Effectiveness Skill - Measure and Optimize Prompt Engineering

Expertise in measuring, testing, and optimizing prompt effectiveness.
"""

MEASUREMENT_PROMPT = """
You are a prompt effectiveness measurement expert. Help design:
- Quality metrics and evaluation frameworks
- Human evaluation rubrics
- Automated scoring systems
- Semantic similarity measures
- Task-specific KPIs

Key Metrics to Consider:
- Output quality (accuracy, relevance, completeness)
- Consistency and reliability
- Latency and efficiency
- User satisfaction
- Cost per output
- Error rates

Ask clarifying questions about:
1. Task type and complexity
2. Evaluation budget
3. Available ground truth
4. Success criteria
"""

A_B_TESTING_PROMPT = """
You are an expert in prompt A/B testing. Advise on:
- Experimental design (control vs variant)
- Sample size calculation
- Statistical significance testing
- Multivariate testing strategies
- Iteration protocols

Testing Framework:
1. Define hypothesis
2. Create prompt variants
3. Randomize assignments
4. Collect metrics
5. Analyze results
6. Implement winner

Ask clarifying questions about:
1. Testing goals
2. Available traffic/queries
3. Testing duration
4. Statistical requirements
"""

OPTIMIZATION_PROMPT = """
You are a prompt optimization expert. Provide strategies for:
- Prompt structure improvement
- Few-shot example selection
- Instruction clarity enhancement
- Context optimization
- Chain-of-thought integration
- Format specification

Optimization Techniques:
- Add/remove instructions
- Adjust example quality/quantity
- Refine context and constraints
- Optimize token usage
- A/B test variations
- Use prompting frameworks (CoT, ReAct, etc.)

Ask clarifying questions about:
1. Current prompt performance
2. Failure modes
3. Model being used
4. Task requirements
"""

ANALYTICS_PROMPT = """
You are a prompt analytics expert. Help design:
- Prompt performance dashboards
- Usage and cost tracking
- Error analysis workflows
- Improvement tracking
- Comparative analysis

Analytics to Track:
- Input/output patterns
- Performance over time
- Cost analysis
- Error categorization
- User feedback
- Model comparison

Ask clarifying questions about:
1. Data availability
2. Stakeholder needs
3. Tool preferences
4. Reporting frequency
"""


def measure_effectiveness(context: str = None):
    """Design prompt measurement strategy."""
    print("📊 Prompt Effectiveness - Measurement")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + MEASUREMENT_PROMPT)
    return MEASUREMENT_PROMPT


def design_ab_test(context: str = None):
    """Design A/B test for prompts."""
    print("📊 Prompt Effectiveness - A/B Testing")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + A_B_TESTING_PROMPT)
    return A_B_TESTING_PROMPT


def optimize_prompt(context: str = None):
    """Optimize prompt engineering."""
    print("📊 Prompt Effectiveness - Optimization")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + OPTIMIZATION_PROMPT)
    return OPTIMIZATION_PROMPT


def setup_analytics(context: str = None):
    """Setup prompt analytics."""
    print("📊 Prompt Effectiveness - Analytics")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + ANALYTICS_PROMPT)
    return ANALYTICS_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prompt Effectiveness - Measure and Optimize")
    parser.add_argument("task", choices=["measure", "abtest", "optimize", "analytics"], help="Task type")
    parser.add_argument("--context", "-c", help="Prompt context")

    args = parser.parse_args()

    if args.task == "measure":
        measure_effectiveness(args.context)
    elif args.task == "abtest":
        design_ab_test(args.context)
    elif args.task == "optimize":
        optimize_prompt(args.context)
    elif args.task == "analytics":
        setup_analytics(args.context)


if __name__ == "__main__":
    main()

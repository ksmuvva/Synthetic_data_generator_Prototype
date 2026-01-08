"""
GenAI System Design Skill - Architecture, Validation, System Design

Expertise in designing production GenAI systems with proper validation
and safety measures.
"""

ARCHITECTURE_PROMPT = """
You are a GenAI system architect. Help design:
- LLM application architecture
- Component decomposition (orchestrator, prompts, tools)
- Data flow and integration patterns
- Scalability strategies
- Fallback and error handling

Ask clarifying questions about:
1. Application type and use case
2. Expected scale and users
3. Integration requirements
4. Cost constraints
"""

VALIDATION_PROMPT = """
You are a GenAI validation expert. Advise on:
- Output validation strategies
- Quality measurement frameworks
- Safety and content moderation
- Hallucination detection
- Human evaluation workflows

Ask clarifying questions about:
1. Risk tolerance
2. Regulatory requirements
3. Available labeled data
4. Evaluation resources
"""

LLM_SELECTION_PROMPT = """
You are an expert in LLM selection and optimization. Help with:
- Model selection (proprietary vs open-source)
- Fine-tuning vs prompting decisions
- Cost-benefit analysis
- Performance optimization
- Context window strategies

Ask clarifying questions about:
1. Task complexity
2. Latency requirements
3. Budget constraints
4. Data privacy requirements
"""


def design_architecture(requirements: str = None):
    """Design GenAI architecture."""
    print("🏗️ GenAI Architect - System Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + ARCHITECTURE_PROMPT)
    return ARCHITECTURE_PROMPT


def design_validation(requirements: str = None):
    """Design validation pipeline."""
    print("🏗️ GenAI Architect - Validation Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + VALIDATION_PROMPT)
    return VALIDATION_PROMPT


def select_llm(requirements: str = None):
    """Select LLM strategy."""
    print("🏗️ GenAI Architect - LLM Selection")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + LLM_SELECTION_PROMPT)
    return LLM_SELECTION_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GenAI System Architect")
    parser.add_argument("task", choices=["architecture", "validation", "llm"], help="Task type")
    parser.add_argument("--requirements", "-r", help="Project requirements")

    args = parser.parse_args()

    if args.task == "architecture":
        design_architecture(args.requirements)
    elif args.task == "validation":
        design_validation(args.requirements)
    elif args.task == "llm":
        select_llm(args.requirements)


if __name__ == "__main__":
    main()

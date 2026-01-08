"""
Vibe Requirements Skill - Requirements Engineering for AI-Assisted Development

Expertise in gathering, refining, and documenting requirements with AI assistance.
"""

GATHERING_PROMPT = """
You are a requirements engineering expert. Help with:
- Elicitation techniques and stakeholder interviews
- Requirement categorization (functional, non-functional)
- Priority and dependency mapping
- Assumption and constraint identification
- Risk assessment

Ask clarifying questions about:
1. Project scope and objectives
2. Stakeholders and users
3. Constraints and deadlines
4. Success criteria
"""

STORY_WRITING_PROMPT = """
You are an expert in writing user stories. Help craft:
- INVEST-compliant user stories
- Acceptance criteria with Gherkin syntax
- Story points and estimation
- Definition of Done
- Story mapping and prioritization

Ask clarifying questions about:
1. User personas and roles
2. User goals and pain points
3. Business value
4. Technical context
"""

SPECIFICATION_PROMPT = """
You are a technical specification expert. Help create:
- Functional specifications
- Non-functional requirements (performance, security, usability)
- API specifications and data models
- System boundaries and interfaces
- Traceability matrices

Ask clarifying questions about:
1. System complexity
2. Integration points
3. Performance SLAs
4. Compliance requirements
"""

AI_REFINEMENT_PROMPT = """
You are an expert in AI-assisted requirement refinement. Leverage AI to:
- Clarify ambiguous requirements
- Generate edge cases and scenarios
- Validate requirement completeness
- Identify missing requirements
- Improve requirement quality

Ask clarifying questions about:
1. Current requirement quality
2. Available AI tools
3. Team AI maturity
4. Quality standards
"""


def gather_requirements(requirements: str = None):
    """Gather and analyze requirements."""
    print("📋 Vibe Requirements - Gathering")
    print("=" * 50)
    if requirements:
        print(f"\nContext: {requirements}")
    print("\n" + GATHERING_PROMPT)
    return GATHERING_PROMPT


def write_stories(requirements: str = None):
    """Write user stories."""
    print("📋 Vibe Requirements - User Stories")
    print("=" * 50)
    if requirements:
        print(f"\nContext: {requirements}")
    print("\n" + STORY_WRITING_PROMPT)
    return STORY_WRITING_PROMPT


def create_specification(requirements: str = None):
    """Create technical specification."""
    print("📋 Vibe Requirements - Specification")
    print("=" * 50)
    if requirements:
        print(f"\nContext: {requirements}")
    print("\n" + SPECIFICATION_PROMPT)
    return SPECIFICATION_PROMPT


def refine_with_ai(requirements: str = None):
    """Refine requirements using AI."""
    print("📋 Vibe Requirements - AI Refinement")
    print("=" * 50)
    if requirements:
        print(f"\nContext: {requirements}")
    print("\n" + AI_REFINEMENT_PROMPT)
    return AI_REFINEMENT_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Vibe Requirements - Requirements Engineering")
    parser.add_argument("task", choices=["gather", "stories", "spec", "refine"], help="Task type")
    parser.add_argument("--context", "-c", help="Project context")

    args = parser.parse_args()

    if args.task == "gather":
        gather_requirements(args.context)
    elif args.task == "stories":
        write_stories(args.context)
    elif args.task == "spec":
        create_specification(args.context)
    elif args.task == "refine":
        refine_with_ai(args.context)


if __name__ == "__main__":
    main()

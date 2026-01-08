"""
Synthetic Data Generator Skill - Training Data, Labeling, Augmentation

Expertise in generating and managing synthetic training data.
"""

GENERATION_PROMPT = """
You are a synthetic data expert. Help design:
- Synthetic data generation strategies
- Statistical pattern preservation
- Privacy-safe data synthesis
- Rare event simulation
- Domain-specific generators

Ask clarifying questions about:
1. Data type and structure
2. Privacy requirements
3. Volume needed
4. Use case (training, testing, augmentation)
"""

AUGMENTATION_PROMPT = """
You are a data augmentation expert. Advise on:
- Text augmentation techniques
- Image/audio/video augmentation
- SMOTE and oversampling strategies
- Domain-specific augmentation
- Augmentation validation

Ask clarifying questions about:
1. Data modality
2. Model sensitivity to augmentation
3. Computational budget
4. Desired diversity
"""

LABELING_PROMPT = """
You are a data labeling workflow expert. Help design:
- Efficient labeling interfaces
- Active learning strategies
- Quality assurance workflows
- Label consistency management
- Tool selection and integration

Ask clarifying questions about:
1. Data volume and complexity
2. Labeler expertise
3. Budget constraints
4. Quality requirements
"""


def generate_synthetic_data(requirements: str = None):
    """Generate synthetic data."""
    print("🔮 Synthetic Data Expert - Generation")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + GENERATION_PROMPT)
    return GENERATION_PROMPT


def augment_data(requirements: str = None):
    """Augment existing data."""
    print("🔮 Synthetic Data Expert - Augmentation")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + AUGMENTATION_PROMPT)
    return AUGMENTATION_PROMPT


def design_labeling(requirements: str = None):
    """Design labeling workflow."""
    print("🔮 Synthetic Data Expert - Labeling Workflow")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + LABELING_PROMPT)
    return LABELING_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Synthetic Data Expert")
    parser.add_argument("task", choices=["generate", "augment", "label"], help="Task type")
    parser.add_argument("--requirements", "-r", help="Project requirements")

    args = parser.parse_args()

    if args.task == "generate":
        generate_synthetic_data(args.requirements)
    elif args.task == "augment":
        augment_data(args.requirements)
    elif args.task == "label":
        design_labeling(args.requirements)


if __name__ == "__main__":
    main()

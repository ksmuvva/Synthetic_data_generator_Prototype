"""
Azure Architect Skill - Comprehensive Azure Expertise

Expertise across all Azure domains including Data, AI, Security, DevOps, and more.
"""

DATA_SERVICES_PROMPT = """
You are an Azure Data Services architect. Expert in:
- Azure Data Lake, Data Factory, Synapse Analytics
- SQL Database, Cosmos DB, PostgreSQL
- Event Hubs, Service Bus, Stream Analytics
- Databricks, HDInsight
- Data integration patterns

Ask clarifying questions about:
1. Data volume and velocity
2. Query patterns and SLAs
3. Integration requirements
4. Compliance and residency
"""

AI_SERVICES_PROMPT = """
You are an Azure AI/ML architect. Expert in:
- Azure OpenAI Service, Cognitive Services
- Azure Machine Learning (MLflow, compute, pipelines)
- Cognitive Search, Form Recognizer
- Bot Service, Translator
- AI deployment patterns

Ask clarifying questions about:
1. Use case complexity
2. Model hosting requirements
3. Customization needs
4. Integration patterns
"""

SECURITY_PROMPT = """
You are an Azure Security architect. Expert in:
- Azure AD, Entra ID, Identity management
- Key Vault, Security Center
- Network security (NSGs, Firewalls, DDoS)
- Governance, Policy, Compliance
- Security monitoring

Ask clarifying questions about:
1. Compliance requirements
2. Identity provider needs
3. Network architecture
4. Data classification
"""

DEVOPS_PROMPT = """
You are an Azure DevOps architect. Expert in:
- Azure DevOps (Boards, Repos, Pipelines)
- GitHub Actions, AKS, Container Apps
- Application Insights, Monitor
- Terraform, Bicep, ARM templates
- CI/CD best practices

Ask clarifying questions about:
1. Team workflow
2. Deployment frequency
3. Environments and stages
4. Existing tools
"""

COST_OPTIMIZATION_PROMPT = """
You are an Azure Cost Optimization expert. Advise on:
- Reserved instances, Spot pricing
- Right-sizing resources
- Cost analysis and budgeting
- Architecture for cost efficiency
- Spending alerts and governance

Ask clarifying questions about:
1. Budget constraints
2. Workload predictability
3. Flexibility requirements
4. Billing and governance
"""


def design_data_solution(requirements: str = None):
    """Design Azure data solution."""
    print("☁️ Azure Architect - Data Services")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + DATA_SERVICES_PROMPT)
    return DATA_SERVICES_PROMPT


def design_ai_solution(requirements: str = None):
    """Design Azure AI/ML solution."""
    print("☁️ Azure Architect - AI/ML Services")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + AI_SERVICES_PROMPT)
    return AI_SERVICES_PROMPT


def design_security(requirements: str = None):
    """Design Azure security solution."""
    print("☁️ Azure Architect - Security")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + SECURITY_PROMPT)
    return SECURITY_PROMPT


def design_devops(requirements: str = None):
    """Design Azure DevOps solution."""
    print("☁️ Azure Architect - DevOps")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + DEVOPS_PROMPT)
    return DEVOPS_PROMPT


def optimize_costs(requirements: str = None):
    """Optimize Azure costs."""
    print("☁️ Azure Architect - Cost Optimization")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + COST_OPTIMIZATION_PROMPT)
    return COST_OPTIMIZATION_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Azure Architect - Comprehensive Azure Expert")
    parser.add_argument("task", choices=["data", "ai", "security", "devops", "cost"], help="Task type")
    parser.add_argument("--requirements", "-r", help="Project requirements")

    args = parser.parse_args()

    if args.task == "data":
        design_data_solution(args.requirements)
    elif args.task == "ai":
        design_ai_solution(args.requirements)
    elif args.task == "security":
        design_security(args.requirements)
    elif args.task == "devops":
        design_devops(args.requirements)
    elif args.task == "cost":
        optimize_costs(args.requirements)


if __name__ == "__main__":
    main()

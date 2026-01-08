"""
Tender Writing Expert Skill - UK Public Sector Tenders

Expertise in G-Cloud, NHS, and Local Government tender writing for the UK public sector.
"""

G_CLOUD_PROMPT = """
You are a G-Cloud framework tender expert. Help with:
- G-Cloud application completion
- Service description writing
- Social value statements (10% weighting)
- Case studies and evidence
- Pricing strategy
- Compliance with Crown Commercial Service requirements

Key G-Cloud Requirements:
- Service descriptions (lots 1-4)
- Social value (Policy alignment, SDGs, community benefits)
- Case studies with measurable outcomes
- Pricing transparency
- Data protection and security

Ask clarifying questions about:
1. Service type and lot
2. Company credentials
3. Past public sector experience
4. Social value initiatives
"""

NHS_PROMPT = """
You are an NHS tender expert. Help with:
- NHS tender response writing
- NHS-specific compliance (DCB0129, IGToolkit)
- Clinical safety and risk management
- NHS Long Term Plan alignment
- Value for money demonstration
- Patient benefit articulation

Key NHS Requirements:
- Health and Social Care Act compliance
- Information Governance Toolkit
- Clinical Safety Officers
- NHS Values alignment
- Patient outcome metrics
- Data security (NHS Data Security Standards)

Ask clarifying questions about:
1. Service/product type
2. Clinical safety requirements
3. IG compliance status
4. NHS experience and references
"""

LOCAL_GOV_PROMPT = """
You are a Local Government tender expert. Help with:
- Local authority bid writing
- Social value maximization (Procurement Policy Note 06/20)
- Community benefit articulation
- Local economic impact
- Sustainability and climate responses
- Equality impact assessments

Key Local Gov Requirements:
- Social Value (PPN 06/20): at least 10% weighting
- Local economic benefits
- Climate change and sustainability
- Equality Act compliance
- Community engagement
- Small business engagement

Ask clarifying questions about:
1. Service type and council
2. Local presence and supply chain
3. Social value initiatives
4. Sustainability credentials
"""

SOCIAL_VALUE_PROMPT = """
You are a social value expert. Help articulate:
- Policy alignment (levelling up, net zero, well-being)
- Measurable social outcomes
- Employment and skills development
- Community investment
- Environmental sustainability
- Innovation and social enterprise

Social Value Themes (from PPN 06/20):
1. COVID-19 recovery
2. Tackling economic inequality
3. Fighting climate change
4. Equal opportunity
5. Well-being
6. Supplier diversity

Ask clarifying questions about:
1. Company social initiatives
2. Community partnerships
3. Environmental commitments
4. Employment practices
"""

SCORING_PROMPT = """
You are a tender scoring expert. Advise on:
- Understanding evaluation criteria
- Weight and scoring optimization
- Evidence quality and structure
- Response length and format
- Common pitfalls to avoid
- Differentiators and USPs

Ask clarifying questions about:
1. Authority and tender
2. Evaluation criteria
3. Score thresholds
4. Competition analysis
"""


def write_gcloud(context: str = None):
    """Write G-Cloud application."""
    print("📝 Tender Expert - G-Cloud Framework")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + G_CLOUD_PROMPT)
    return G_CLOUD_PROMPT


def write_nhs(context: str = None):
    """Write NHS tender response."""
    print("📝 Tender Expert - NHS Tender")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + NHS_PROMPT)
    return NHS_PROMPT


def write_local_gov(context: str = None):
    """Write Local Government tender response."""
    print("📝 Tender Expert - Local Government")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + LOCAL_GOV_PROMPT)
    return LOCAL_GOV_PROMPT


def write_social_value(context: str = None):
    """Write social value statement."""
    print("📝 Tender Expert - Social Value")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + SOCIAL_VALUE_PROMPT)
    return SOCIAL_VALUE_PROMPT


def optimize_scoring(context: str = None):
    """Optimize for tender scoring."""
    print("📝 Tender Expert - Scoring Strategy")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + SCORING_PROMPT)
    return SCORING_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Tender Writing Expert - UK Public Sector")
    parser.add_argument("task", choices=["gcloud", "nhs", "localgov", "socialvalue", "scoring"], help="Tender type")
    parser.add_argument("--context", "-c", help="Tender context")

    args = parser.parse_args()

    if args.task == "gcloud":
        write_gcloud(args.context)
    elif args.task == "nhs":
        write_nhs(args.context)
    elif args.task == "localgov":
        write_local_gov(args.context)
    elif args.task == "socialvalue":
        write_social_value(args.context)
    elif args.task == "scoring":
        optimize_scoring(args.context)


if __name__ == "__main__":
    main()

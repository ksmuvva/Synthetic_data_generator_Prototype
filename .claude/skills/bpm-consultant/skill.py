"""
BPM Consultant Skill - Business Process Management, BPMN, Process Optimization

Expertise in business process analysis, modeling, and optimization.
"""

PROCESS_DISCOVERY_PROMPT = """
You are a business process consultant. Help discover:
- Current state processes (as-is)
- Stakeholder mapping
- Process touchpoints and handoffs
- Pain points and bottlenecks
- Improvement opportunities

Ask clarifying questions about:
1. Process scope and boundaries
2. Stakeholders and participants
3. Current documentation
4. Pain points and goals
"""

BPMN_DESIGN_PROMPT = """
You are a BPMN modeling expert. Help design:
- BPMN 2.0 compliant diagrams
- Process flows and gateways
- Events, activities, and tasks
- Pools, lanes, and collaborations
- Process hierarchies

Ask clarifying questions about:
1. Process complexity
2. Stakeholder visibility needs
3. Level of detail required
4. Tool preferences
"""

OPTIMIZATION_PROMPT = """
You are a process optimization expert. Advise on:
- Value stream mapping
- Waste elimination (Lean)
- Cycle time reduction
- Resource optimization
- Automation opportunities

Ask clarifying questions about:
1. Current process metrics
2. Improvement goals
3. Constraints and risks
4. Budget and timeline
"""

AUTOMATION_PROMPT = """
You are a workflow automation expert. Help design:
- Automation strategy and roadmap
- Tool selection (RPA, iPaaS, BPM suites)
- Integration architecture
- Change management
- ROI calculation

Ask clarifying questions about:
1. Process volume and frequency
2. System integrations needed
3. Technical capabilities
4. Budget and timeline
"""


def discover_processes(context: str = None):
    """Discover business processes."""
    print("🔄 BPM Consultant - Process Discovery")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + PROCESS_DISCOVERY_PROMPT)
    return PROCESS_DISCOVERY_PROMPT


def design_bpmn(context: str = None):
    """Design BPMN diagrams."""
    print("🔄 BPM Consultant - BPMN Design")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + BPMN_DESIGN_PROMPT)
    return BPMN_DESIGN_PROMPT


def optimize_process(context: str = None):
    """Optimize business process."""
    print("🔄 BPM Consultant - Process Optimization")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + OPTIMIZATION_PROMPT)
    return OPTIMIZATION_PROMPT


def automate_workflow(context: str = None):
    """Design workflow automation."""
    print("🔄 BPM Consultant - Workflow Automation")
    print("=" * 50)
    if context:
        print(f"\nContext: {context}")
    print("\n" + AUTOMATION_PROMPT)
    return AUTOMATION_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="BPM Consultant - Business Process Management")
    parser.add_argument("task", choices=["discover", "bpmn", "optimize", "automate"], help="Task type")
    parser.add_argument("--context", "-c", help="Business context")

    args = parser.parse_args()

    if args.task == "discover":
        discover_processes(args.context)
    elif args.task == "bpmn":
        design_bpmn(args.context)
    elif args.task == "optimize":
        optimize_process(args.context)
    elif args.task == "automate":
        automate_workflow(args.context)


if __name__ == "__main__":
    main()

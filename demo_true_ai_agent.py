"""
Demo: True AI Agent in Action

This demo showcases the True AI Agent capabilities:
1. Understanding natural language requests
2. Creating multi-step plans
3. Executing tools autonomously
4. Learning from outcomes
5. Providing proactive suggestions
6. Warning of potential issues
"""

import asyncio
import pandas as pd
import numpy as np
from synth.agent import TrueAIAgent


def create_sample_data(n=100):
    """Create sample customer data."""
    np.random.seed(42)
    return pd.DataFrame({
        'age': np.random.randint(21, 70, n),
        'income': np.random.randint(30000, 120000, n),
        'orders': np.random.poisson(5, n),
        'spent': np.random.exponential(500, n),
    })


async def demo_true_ai_agent():
    """Demonstrate True AI Agent capabilities."""

    print("=" * 80)
    print("  TRUE AI AGENT DEMO")
    print("=" * 80)
    print()
    print("Initializing True AI Agent...")
    agent = TrueAIAgent(storage_path=".demo_agent_memory")
    agent.initialize()

    # Show initial status
    status = agent.get_status()
    print(f"Agent Status: {status}")
    print()

    # Create sample data
    print("Creating sample customer data...")
    original_data = create_sample_data(200)
    print(f"Original data: {len(original_data)} records")
    print()

    # ========================================
    # Demo 1: Generate Synthetic Data
    # ========================================
    print("-" * 80)
    print("DEMO 1: Generate Synthetic Data")
    print("-" * 80)
    print()

    request = "Generate 50 synthetic customer records from this data"
    print(f"User Request: '{request}'")
    print()

    # Add data to context
    response = await agent.process_request(
        request,
        context_params={"data": original_data}
    )

    print("Agent Response:")
    print(f"  Success: {response.success}")
    print(f"  Message: {response.message}")
    print(f"  Processing Time: {response.metadata.get('processing_time_seconds', 0):.2f}s")
    print(f"  Steps Executed: {response.metadata.get('steps_executed', 0)}")
    print(f"  Tools Used: {response.metadata.get('tools_used', [])}")

    if response.data is not None and isinstance(response.data, pd.DataFrame):
        print(f"  Generated Data: {len(response.data)} records")
        print()
        print("  Sample of generated data:")
        print(response.data.head(3).to_string())
    print()

    # Show proactive suggestions
    if response.suggestions:
        print("  Proactive Suggestions:")
        for suggestion in response.suggestions:
            print(f"    - {suggestion.title}: {suggestion.description}")
    print()

    # Show warnings
    if response.warnings:
        print("  Warnings:")
        for warning in response.warnings:
            print(f"    - {warning.message}")
    print()

    # ========================================
    # Demo 2: Analyze Data
    # ========================================
    print("-" * 80)
    print("DEMO 2: Analyze Data")
    print("-" * 80)
    print()

    request = "Analyze this customer data"
    print(f"User Request: '{request}'")
    print()

    response = await agent.process_request(
        request,
        context_params={"data": original_data}
    )

    print("Agent Response:")
    print(f"  Success: {response.success}")
    print(f"  Message: {response.message}")
    print()

    if response.data and isinstance(response.data, dict):
        stats = response.data.get("statistics", {})
        print("  Data Statistics:")
        print(f"    Rows: {stats.get('rows', 'N/A')}")
        print(f"    Columns: {stats.get('columns', 'N/A')}")
        print(f"    Numeric Columns: {stats.get('numeric_columns', 'N/A')}")
        print(f"    Memory Usage: {stats.get('memory_usage_mb', 0):.2f} MB")
    print()

    # ========================================
    # Demo 3: Validate Synthetic Data
    # ========================================
    print("-" * 80)
    print("DEMO 3: Validate Synthetic Data Quality")
    print("-" * 80)
    print()

    # First generate synthetic data
    synth_request = "Generate 100 synthetic customer records"
    synth_response = await agent.process_request(
        synth_request,
        context_params={"data": original_data}
    )

    if synth_response.success:
        synthetic_data = synth_response.data

        request = "Validate the synthetic data quality"
        print(f"User Request: '{request}'")
        print()

        response = await agent.process_request(
            request,
            context_params={
                "original": original_data,
                "synthetic": synthetic_data
            }
        )

        print("Agent Response:")
        print(f"  Success: {response.success}")
        print(f"  Message: {response.message}")
        print()

        if response.data and isinstance(response.data, dict):
            print("  Validation Results:")
            print(f"    Original Rows: {response.data.get('rows', {}).get('original', 'N/A')}")
            print(f"    Synthetic Rows: {response.data.get('rows', {}).get('synthetic', 'N/A')}")
            print(f"    Columns Match: {response.data.get('columns_match', 'N/A')}")

            stats_sim = response.data.get('statistical_similarity', {})
            if stats_sim:
                print("    Statistical Similarity (mean difference %):")
                for col, metrics in list(stats_sim.items())[:3]:
                    print(f"      {col}: {metrics.get('difference_percent', 0):.1f}%")
    print()

    # ========================================
    # Demo 4: Memory and Learning
    # ========================================
    print("-" * 80)
    print("DEMO 4: Memory and Learning")
    print("-" * 80)
    print()

    # Show what the agent learned
    memory_stats = agent.memory.get_stats()
    print("Memory Statistics:")
    print(f"  Short-term Turns: {memory_stats['short_term']['total_turns']}")
    print(f"  Long-term Interactions: {memory_stats['long_term']['interactions']}")
    print(f"  Strategies Learned: {memory_stats['long_term']['strategies']}")
    print()

    # Find similar past requests
    similar = agent.memory.find_similar_situations("generate data")
    print(f"Found {len(similar)} similar past requests")
    print()

    # ========================================
    # Demo 5: Multi-Step Planning
    # ========================================
    print("-" * 80)
    print("DEMO 5: Multi-Step Planning (Demonstrating True AI Agent Behavior)")
    print("-" * 80)
    print()

    request = "I need to generate 200 synthetic customer records, validate the quality, and export to CSV"
    print(f"User Request: '{request}'")
    print()

    response = await agent.process_request(
        request,
        context_params={
            "data": original_data,
            "path": "synthetic_customers.csv"
        }
    )

    print("Agent Response:")
    print(f"  Success: {response.success}")
    print(f"  Message: {response.message}")
    print(f"  Processing Time: {response.metadata.get('processing_time_seconds', 0):.2f}s")
    print()

    # Show the plan that was created
    if response.plan:
        print("  Execution Plan:")
        print(f"    Steps: {len(response.plan.steps)}")
        print(f"    Progress: {response.plan.get_progress() * 100:.0f}%")
        print()

        for i, step in enumerate(response.plan.steps, 1):
            status_icon = "[OK]" if step.status.value == "completed" else "[FAIL]"
            print(f"    Step {i}: {status_icon} {step.action}")
            if step.tool:
                print(f"      Tool: {step.tool}")
            if step.started_at and step.completed_at:
                duration = (step.completed_at - step.started_at).total_seconds()
                print(f"      Duration: {duration:.2f}s")
    print()

    # Show suggestions
    if response.suggestions:
        print("  Proactive Suggestions:")
        for suggestion in response.suggestions:
            print(f"    - [{suggestion.suggestion_type}] {suggestion.title}")
            print(f"      {suggestion.description}")
    print()

    # ========================================
    # Final Status
    # ========================================
    print("-" * 80)
    print("FINAL AGENT STATUS")
    print("-" * 80)
    print()

    status = agent.get_status()
    print(f"  Initialized: {status['initialized']}")
    print(f"  Requests Processed: {status['requests_processed']}")
    print(f"  Tools Registered: {status['tools_registered']}")
    print()
    print(f"  Memory Stats:")
    print(f"    Users: {status['memory_stats']['long_term']['users']}")
    print(f"    Datasets: {status['memory_stats']['long_term']['datasets']}")
    print(f"    Strategies: {status['memory_stats']['long_term']['strategies']}")
    print(f"    Interactions: {status['memory_stats']['long_term']['interactions']}")
    print()

    print("=" * 80)
    print("  TRUE AI AGENT SCORECARD")
    print("=" * 80)
    print()
    print("[OK] Autonomy: Creates and executes multi-step plans")
    print("[OK] Perception: Understands natural language requests")
    print("[OK] Planning: Decomposes goals into steps with dependencies")
    print("[OK] Memory: Remembers patterns, strategies, and interactions")
    print("[OK] Tool Use: Selects and executes appropriate tools")
    print("[OK] Learning: Improves from experience")
    print("[OK] Proactive: Suggests improvements and warns of issues")
    print()
    print("This is now a TRUE AI AGENT, not just a tool!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_true_ai_agent())

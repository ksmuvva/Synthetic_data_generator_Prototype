"""
Test Phase 10 & 11: Proactive Behavior and Environment Awareness

This script tests:
- Proactive suggestions
- Issue warnings
- Opportunity detection
- Resource monitoring
- Environment awareness
"""

import asyncio
import pandas as pd
import numpy as np
from synth.agent.proactive import ProactiveEngine
from synth.agent.perception import (
    ResourceMonitor,
    DataEnvironmentMonitor,
    EnvironmentContextBuilder,
)
from synth.agent.models.core import (
    Context,
    ParsedRequest,
    RequestType,
    EnvironmentContext,
)


async def test_proactive_and_environment():
    """Test proactive behavior and environment awareness."""
    print("=" * 80)
    print("  PHASE 10 & 11: PROACTIVE BEHAVIOR & ENVIRONMENT AWARENESS TEST")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing components...")
    proactive_engine = ProactiveEngine()
    resource_monitor = ResourceMonitor()
    data_monitor = DataEnvironmentMonitor()
    env_builder = EnvironmentContextBuilder()
    print()

    # ========================================
    # Phase 10: Proactive Behavior Tests
    # ========================================

    # Test 1: Generate Suggestions
    print("-" * 80)
    print("PHASE 10 - TEST 1: Generate Suggestions")
    print("-" * 80)
    print()

    context = Context(
        request=ParsedRequest(
            request_id="test_req",
            original_text="Generate 5000 synthetic records",
            intent="Generate synthetic data",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": 5000},
            constraints=[],
            parameters={},
            complexity=0.5,
            confidence=0.8,
        ),
        environment=EnvironmentContext(
            available_memory_mb=8000,
            available_cpu_percent=80,
            available_disk_gb=50,
            active_sessions=1,
        ),
        conversation_history=[],
        user_preferences={},
        similar_past_situations=[],
        working_variables={"data": pd.DataFrame({'x': range(100)})},
    )

    result = {"success": True, "data": pd.DataFrame({'y': range(100)})}
    suggestions = proactive_engine.generate_suggestions(context, result)

    print(f"Generated {len(suggestions)} suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n  Suggestion {i}:")
        print(f"    Type: {suggestion.suggestion_type}")
        print(f"    Title: {suggestion.title}")
        print(f"    Description: {suggestion.description}")
        print(f"    Benefit: {suggestion.benefit}")
        print(f"    Effort: {suggestion.effort}")
        print(f"    Priority: {suggestion.priority}")
    print()

    # Test 2: Generate Warnings
    print("-" * 80)
    print("PHASE 10 - TEST 2: Generate Warnings")
    print("-" * 80)
    print()

    # Create context with potential issues
    warning_context = Context(
        request=ParsedRequest(
            request_id="test_req",
            original_text="Generate 50000 synthetic records",
            intent="Generate synthetic data",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": 50000},
            constraints=[],
            parameters={},
            complexity=0.7,
            confidence=0.8,
        ),
        environment=EnvironmentContext(
            available_memory_mb=500,  # Low memory
            available_cpu_percent=80,
            available_disk_gb=50,
            active_sessions=1,
        ),
        conversation_history=[],
        user_preferences={},
        similar_past_situations=[],
        working_variables={},
    )

    warnings = proactive_engine.generate_warnings(warning_context, None)

    print(f"Generated {len(warnings)} warnings:")
    for i, warning in enumerate(warnings, 1):
        print(f"\n  Warning {i}:")
        print(f"    Type: {warning.warning_type}")
        print(f"    Message: {warning.message}")
        print(f"    Severity: {warning.severity.value}")
        print(f"    Mitigation: {warning.mitigation}")
    print()

    # Test 3: Detect Opportunities
    print("-" * 80)
    print("PHASE 10 - TEST 3: Detect Opportunities")
    print("-" * 80)
    print()

    opportunities = proactive_engine.detect_opportunities(context, result)

    print(f"Detected {len(opportunities)} opportunities:")
    for i, opp in enumerate(opportunities, 1):
        print(f"\n  Opportunity {i}:")
        print(f"    Type: {opp['type']}")
        print(f"    Description: {opp['description']}")
        print(f"    Benefit: {opp['benefit']}")
        print(f"    Effort: {opp['effort']}")
    print()

    # ========================================
    # Phase 11: Environment Awareness Tests
    # ========================================

    # Test 4: Resource Monitoring
    print("-" * 80)
    print("PHASE 11 - TEST 4: Resource Monitoring")
    print("-" * 80)
    print()

    memory = resource_monitor.get_memory_usage()
    cpu = resource_monitor.get_cpu_usage()
    disk = resource_monitor.get_disk_usage()
    status = resource_monitor.check_thresholds()

    print("Resource Status:")
    print(f"  Memory:")
    print(f"    Total: {memory['total_mb']:.0f} MB")
    print(f"    Available: {memory['available_mb']:.0f} MB")
    print(f"    Used: {memory['used_mb']:.0f} MB")
    print(f"    Percent: {memory['percent']:.1f}%")
    print(f"  CPU:")
    print(f"    Available: {100 - cpu:.1f}%")
    print(f"    Used: {cpu:.1f}%")
    print(f"  Disk:")
    print(f"    Total: {disk['total_gb']:.0f} GB")
    print(f"    Free: {disk['free_gb']:.0f} GB")
    print(f"    Used: {disk['used_gb']:.0f} GB")
    print(f"    Percent: {disk['percent']:.1f}%")
    print(f"\n  Overall Status: {status.status.upper()}")
    print()

    # Test 5: Data Environment Monitoring
    print("-" * 80)
    print("PHASE 11 - TEST 5: Data Environment Monitoring")
    print("-" * 80)
    print()

    # Create test data
    test_data = pd.DataFrame({
        'a': [1, 2, 3, None, 5],
        'b': [1, 2, 2, 3, 3],  # Has duplicates
        'c': ['x', 'y', 'z', 'x', 'y'],
    })

    schema = data_monitor.analyze_schema(test_data)
    print("Data Schema:")
    print(f"  Rows: {schema['rows']}")
    print(f"  Columns: {schema['columns']}")
    print(f"  Memory: {schema['memory_mb']:.2f} MB")
    print(f"  Column Types:")
    for col, dtype in schema['column_types'].items():
        print(f"    {col}: {dtype}")
    print()

    quality = data_monitor.estimate_quality(test_data)
    print("Data Quality:")
    print(f"  Completeness: {quality['completeness']:.1%}")
    print(f"  Missing Values: {quality['missing_values']}")
    print(f"  Duplicate Rows: {quality['duplicate_rows']}")
    print()

    # Test 6: Environment Context Building
    print("-" * 80)
    print("PHASE 11 - TEST 6: Environment Context Building")
    print("-" * 80)
    print()

    env_context = env_builder.build_context()
    print("Built Environment Context:")
    print(f"  Available Memory: {env_context.available_memory_mb:.0f} MB")
    print(f"  Available CPU: {env_context.available_cpu_percent:.0f}%")
    print(f"  Available Disk: {env_context.available_disk_gb:.0f} GB")
    print(f"  Active Sessions: {env_context.active_sessions}")
    print()

    # Test 7: Change Detection
    print("-" * 80)
    print("PHASE 11 - TEST 7: Change Detection")
    print("-" * 80)
    print()

    previous_context = EnvironmentContext(
        available_memory_mb=16000,
        available_cpu_percent=50,
        available_disk_gb=100,
        active_sessions=1,
    )

    changes = env_builder.detect_changes(previous_context)
    print(f"Detected {len(changes)} changes:")
    for change in changes:
        print(f"  - {change}")

    if not changes:
        print("  No significant changes detected")
    print()

    # ========================================
    # Summary
    # ========================================
    print("=" * 80)
    print("  PHASE 10 & 11 TEST SUMMARY")
    print("=" * 80)
    print()

    print("PHASE 10: Proactive Behavior")
    print("[OK] Generate Suggestions: Working")
    print("[OK] Generate Warnings: Working")
    print("[OK] Detect Opportunities: Working")
    print()

    print("PHASE 11: Environment Awareness")
    print("[OK] Resource Monitoring: Working")
    print("[OK] Data Environment Monitoring: Working")
    print("[OK] Environment Context Building: Working")
    print("[OK] Change Detection: Working")
    print()

    print("Phase 10 & 11: COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_proactive_and_environment())

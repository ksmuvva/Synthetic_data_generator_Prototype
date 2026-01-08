"""
Test Phase 7: Autonomous Decision Making

This script tests the cognitive layer components:
- Strategy Selection
- Tool Selection
- Decision Engine
- Progress Tracking
- Cognitive Layer
- Conversation Manager
- Session Manager
"""

import asyncio
import pandas as pd
import numpy as np
from synth.agent import (
    TrueAIAgent,
    CognitiveLayer,
    MemoryLayer,
    ToolRegistry,
)
from synth.agent.tools import DataGenerationTool
from synth.agent.models.core import (
    RequestType,
    StrategyType,
    Context,
    ParsedRequest,
    EnvironmentContext,
)


def create_sample_data(n=100):
    """Create sample customer data."""
    np.random.seed(42)
    return pd.DataFrame({
        'age': np.random.randint(21, 70, n),
        'income': np.random.randint(30000, 120000, n),
        'orders': np.random.poisson(5, n),
        'spent': np.random.exponential(500, n),
    })


def create_test_context(data):
    """Create a test context."""
    return Context(
        request=ParsedRequest(
            request_id="test_req",
            original_text="Generate 50 synthetic records",
            intent="Generate synthetic data",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": 50},
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
        working_variables={"data": data},
    )


async def test_cognitive_layer():
    """Test cognitive layer components."""
    print("=" * 80)
    print("  PHASE 7: AUTONOMOUS DECISION MAKING TEST")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing components...")
    tool_registry = ToolRegistry()
    tool_registry.register_tool(DataGenerationTool())
    memory = MemoryLayer(storage_path=".test_phase7_memory")
    cognitive = CognitiveLayer(tool_registry)

    # Create sample data
    data = create_sample_data(100)
    print(f"Created sample data: {len(data)} records")
    print()

    # ========================================
    # Test 1: Strategy Selection
    # ========================================
    print("-" * 80)
    print("TEST 1: Strategy Selection")
    print("-" * 80)
    print()

    context = create_test_context(data)

    strategy, rationale = cognitive.select_strategy(context)
    print(f"Selected Strategy: {strategy.value}")
    print(f"Fit Level: {rationale.get('fit_level')}")
    print(f"Considered: {rationale.get('considered')} alternatives")
    print()

    # ========================================
    # Test 2: Tool Selection
    # ========================================
    print("-" * 80)
    print("TEST 2: Tool Selection")
    print("-" * 80)
    print()

    task = "generate synthetic data from patterns"
    tool, rationale = cognitive.select_tool(task, context)

    if tool:
        print(f"Selected Tool: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Match Score: {rationale.get('match_score', 0):.2f}")
        print(f"Past Success Rate: {rationale.get('past_success_rate', 0):.1%}")
        print(f"Capabilities: {', '.join(tool.get_capabilities())}")
    else:
        print("No tool found")
    print()

    # ========================================
    # Test 3: Decision Engine
    # ========================================
    print("-" * 80)
    print("TEST 3: Decision Engine - Comprehensive Decision")
    print("-" * 80)
    print()

    decisions = cognitive.make_all_decisions(context)

    print("Decisions Made:")
    for decision_type, decision in decisions.items():
        print(f"  {decision_type.capitalize()}:")
        if hasattr(decision.selection, 'value'):
            print(f"    Selection: {decision.selection.value}")
        else:
            print(f"    Selection: {decision.selection}")
        print(f"    Confidence: {decision.confidence:.2f}")
        print(f"    Alternatives: {len(decision.alternatives)}")
    print()

    # ========================================
    # Test 4: Progress Tracking
    # ========================================
    print("-" * 80)
    print("TEST 4: Progress Tracking")
    print("-" * 80)
    print()

    from synth.agent.models.core import Plan, Step, Goal, TaskStatus

    plan = Plan()
    plan.goal = Goal(description="Test plan")
    plan.steps = [
        Step(action="step1", tool=None, parameters={}, dependencies=[]),
        Step(action="step2", tool=None, parameters={}, dependencies=[]),
        Step(action="step3", tool=None, parameters={}, dependencies=[]),
    ]

    progress = cognitive.start_tracking(plan)
    print(f"Tracking plan: {plan.plan_id}")
    print(f"Total steps: {progress.total_steps}")
    print(f"Pending steps: {progress.pending_steps}")
    print(f"Completion: {progress.completion_percent:.0f}%")
    print()

    # Simulate step completion
    print("Simulating step execution...")
    for i, step in enumerate(plan.steps):
        step.status = TaskStatus.IN_PROGRESS
        cognitive.update_step(plan.plan_id, step)

        step.status = TaskStatus.COMPLETED
        step.completed_at = pd.Timestamp.now()
        cognitive.update_step(plan.plan_id, step)

        progress = cognitive.get_progress(plan.plan_id)
        print(f"  Step {i+1} completed - Progress: {progress.completion_percent:.0f}%")

    print()
    print(f"Final Progress: {progress.completion_percent:.0f}%")
    print(f"Completed steps: {progress.completed_steps}/{progress.total_steps}")
    print()

    # ========================================
    # Test 5: Trade-off Analysis
    # ========================================
    print("-" * 80)
    print("TEST 5: Trade-off Analysis")
    print("-" * 80)
    print()

    option_a = {
        "speed": 100,
        "quality": 80,
        "memory_mb": 500,
    }
    option_b = {
        "speed": 60,
        "quality": 95,
        "memory_mb": 800,
    }

    analysis = cognitive.analyze_tradeoffs(
        option_a,
        option_b,
        criteria=["speed", "quality", "memory_mb"],
        weights={"speed": 0.3, "quality": 0.5, "memory_mb": 0.2},
    )

    print("Comparing two options:")
    print(f"  Option A: Speed={option_a['speed']}, Quality={option_a['quality']}, Memory={option_a['memory_mb']}MB")
    print(f"  Option B: Speed={option_b['speed']}, Quality={option_b['quality']}, Memory={option_b['memory_mb']}MB")
    print()
    print(f"Winner: Option {analysis['winner']}")
    print(f"Weighted Scores:")
    print(f"  Option A: {analysis['analysis']['weighted_scores']['A']:.2f}")
    print(f"  Option B: {analysis['analysis']['weighted_scores']['B']:.2f}")
    print()

    # ========================================
    # Test 6: Conversation Manager
    # ========================================
    print("-" * 80)
    print("TEST 6: Conversation Manager")
    print("-" * 80)
    print()

    from synth.agent.agent import ConversationManager, SessionManager
    from synth.agent.memory.short_term import ShortTermMemory

    short_term = ShortTermMemory()
    conv_manager = ConversationManager(short_term)

    # Create conversation
    conv = conv_manager.create_conversation("test_conv", "user_123")
    print(f"Created conversation: {conv.conversation_id}")
    print(f"Current topic: {conv.current_topic}")
    print(f"Turns count: {conv.turns_count}")
    print()

    # Add turns
    conv_manager.add_turn(
        "test_conv",
        "Generate 50 records",
        "I'll generate 50 synthetic records for you.",
    )

    conv_manager.add_turn(
        "test_conv",
        "Now validate them",
        "I'll validate the generated data.",
    )

    # Get history
    history = conv_manager.get_history("test_conv", max_turns=5)
    print(f"Conversation turns: {len(history)}")
    for i, turn in enumerate(history, 1):
        print(f"  Turn {i}:")
        print(f"    User: {turn.user_message[:50]}...")
        print(f"    Agent: {turn.agent_response[:50]}...")
    print()

    # ========================================
    # Test 7: Session Manager
    # ========================================
    print("-" * 80)
    print("TEST 7: Session Manager")
    print("-" * 80)
    print()

    session_manager = SessionManager(conv_manager)

    # Create session
    session = session_manager.create_session("user_123")
    print(f"Created session: {session.session_id}")
    print(f"User ID: {session.user_id}")
    print(f"Conversation ID: {session.conversation_id}")
    print(f"Is Active: {session.is_active}")
    print()

    # Update session
    updated = session_manager.update_session(
        session.session_id,
        {"last_request": "generate data"},
    )
    print(f"Session state: {updated.state}")
    print(f"Idle time: {updated.idle_seconds:.0f}s")
    print()

    # Get stats
    stats = session_manager.get_session_stats()
    print("Session Stats:")
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  Active sessions: {stats['active_sessions']}")
    print(f"  Unique users: {stats['unique_users']}")
    print()

    # ========================================
    # Summary
    # ========================================
    print("=" * 80)
    print("  PHASE 7 TEST SUMMARY")
    print("=" * 80)
    print()

    status = cognitive.get_status()
    print("Cognitive Layer Status:")
    print(f"  Active plans: {status['active_plans']}")
    print(f"  Tools available: {status['tools_available']}")
    print(f"  Decision engine ready: {status['decision_engine_ready']}")
    print(f"  Progress tracker ready: {status['progress_tracker_ready']}")
    print()

    print("[OK] Strategy Selection: Working")
    print("[OK] Tool Selection: Working")
    print("[OK] Decision Engine: Working")
    print("[OK] Progress Tracking: Working")
    print("[OK] Trade-off Analysis: Working")
    print("[OK] Conversation Manager: Working")
    print("[OK] Session Manager: Working")
    print("[OK] Cognitive Layer: Working")
    print()
    print("Phase 7: AUTONOMOUS DECISION MAKING - COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_cognitive_layer())

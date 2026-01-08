"""Quick integration test for the 4 features."""
import asyncio
from synth.agent import TrueAIAgent

async def test():
    print("=" * 60)
    print("INTEGRATION TEST: 4 Advanced Features")
    print("=" * 60)

    agent = TrueAIAgent(storage_path='.test_integration')
    agent.initialize()

    print("\n[1] Intent Disambiguation:", "OK" if agent.intent_disambiguator else "MISSING")
    print("[2] Self-Correction:", "OK" if agent.correction_engine else "MISSING")
    print("[3] Causal Reasoning:", "OK" if agent.causal_reasoning else "MISSING")
    print("[4] Adaptive Learning:", "OK" if agent.adaptive_learning else "MISSING")

    all_ok = all([
        agent.intent_disambiguator,
        agent.correction_engine,
        agent.causal_reasoning,
        agent.adaptive_learning
    ])

    print("\n" + "=" * 60)
    if all_ok:
        print("All 4 features initialized and integrated!")
    else:
        print("Some features are missing!")
    print("=" * 60)

asyncio.run(test())

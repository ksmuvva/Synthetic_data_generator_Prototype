"""
AI Engineer Skill - GenAI Systems, RAG, AI Agents, Production Deployment

This skill provides expertise in building production-ready AI systems including
RAG architectures, AI agents, and scalable LLM deployments.
"""

import sys
from pathlib import Path

# System prompts for different AI engineering tasks
RAG_DESIGN_PROMPT = """
You are an expert RAG (Retrieval-Augmented Generation) architect. Help design:
- Document ingestion pipelines
- Embedding strategies and vector stores
- Retrieval optimization (chunking, indexing, re-ranking)
- Context window management
- Evaluation metrics for RAG quality

Ask clarifying questions about:
1. Data sources and volume
2. Expected query patterns
3. Latency requirements
4. Accuracy requirements
"""

AGENT_DESIGN_PROMPT = """
You are an expert AI agent architect. Help design:
- Multi-agent systems
- Tool/function calling patterns
- Memory and context management
- Agent orchestration frameworks
- State management and persistence

Ask clarifying questions about:
1. Agent responsibilities and goals
2. Available tools and APIs
3. Human-in-the-loop requirements
4. Error handling and fallback strategies
"""

DEPLOYMENT_PROMPT = """
You are an expert in AI/ML production deployment. Advise on:
- Model serving infrastructure
- Scaling strategies (GPU/CPU optimization)
- API design and rate limiting
- Monitoring and observability
- Cost optimization

Ask clarifying questions about:
1. Expected traffic volume
2. Latency SLAs
3. Budget constraints
4. Compliance requirements
"""


def design_rag_system(requirements: str = None):
    """Design a RAG system based on requirements."""
    print("🤖 AI Engineer - RAG System Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + RAG_DESIGN_PROMPT)
    return RAG_DESIGN_PROMPT


def design_agent_system(requirements: str = None):
    """Design an AI agent system."""
    print("🤖 AI Engineer - Agent System Design")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + AGENT_DESIGN_PROMPT)
    return AGENT_DESIGN_PROMPT


def plan_deployment(requirements: str = None):
    """Plan production deployment strategy."""
    print("🤖 AI Engineer - Production Deployment")
    print("=" * 50)
    if requirements:
        print(f"\nRequirements: {requirements}")
    print("\n" + DEPLOYMENT_PROMPT)
    return DEPLOYMENT_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Engineer - GenAI Systems Expert")
    parser.add_argument("task", choices=["rag", "agent", "deploy"], help="Task type")
    parser.add_argument("--requirements", "-r", help="Project requirements")

    args = parser.parse_args()

    if args.task == "rag":
        design_rag_system(args.requirements)
    elif args.task == "agent":
        design_agent_system(args.requirements)
    elif args.task == "deploy":
        plan_deployment(args.requirements)


if __name__ == "__main__":
    main()

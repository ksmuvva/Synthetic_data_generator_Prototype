"""
Advanced Reasoning Skill - Complex Problem-Solving with Systematic Frameworks

Expertise in Chain of Thought, Tree of Thoughts, MCTS, and other reasoning frameworks.
"""

CHAIN_OF_THOUGHT_PROMPT = """
You are an expert in Chain of Thought (CoT) reasoning. Guide through:
- Step-by-step logical decomposition
- Intermediate reasoning verification
- Thought process documentation
- Assumption explicitation
- Conclusion validation

Framework:
1. Break down the problem
2. Identify key components
3. Reason through each step
4. Verify intermediate conclusions
5. Synthesize final answer

Ask clarifying questions about:
1. Problem domain
2. Available information
3. Desired output format
4. Confidence requirements
"""

TREE_OF_THOUGHTS_PROMPT = """
You are an expert in Tree of Thoughts (ToT) exploration. Guide through:
- Generating multiple solution branches
- Evaluating and pruning branches
- Backtracking and exploration
- Heuristic evaluation
- Optimal path selection

Framework:
1. Generate initial thoughts/solutions
2. Explore each branch systematically
3. Evaluate promise of each branch
4. Decide: continue, backtrack, or conclude
5. Select best solution path

Ask clarifying questions about:
1. Exploration budget
2. Evaluation criteria
3. Risk tolerance
4. Time constraints
"""

MCTS_PROMPT = """
You are an expert in Monte Carlo Tree Search (MCTS) reasoning. Guide through:
- State space representation
- Tree policy (selection + expansion)
- Rollout simulation
- Backpropagation
- Iterative improvement

Framework:
1. Selection: Choose promising node using UCB
2. Expansion: Add new child nodes
3. Simulation: Rollout to terminal state
4. Backpropagation: Update statistics
5. Repeat and converge

Ask clarifying questions about:
1. Decision complexity
2. Simulation budget
3. Evaluation function
4. Exploration vs exploitation
"""

DECOMPOSITION_PROMPT = """
You are an expert in problem decomposition. Help with:
- Divide and conquer strategies
- Hierarchical task networks
- Dependency identification
- Parallelization opportunities
- Integration planning

Framework:
1. Identify main problem
2. Decompose into subproblems
3. Identify dependencies
4. Solve subproblems
5. Integrate solutions

Ask clarifying questions about:
1. Problem type and scale
2. Available resources
3. Time constraints
4. Quality requirements
"""


def chain_of_thought(problem: str = None):
    """Apply Chain of Thought reasoning."""
    print("🧠 Advanced Reasoning - Chain of Thought")
    print("=" * 50)
    if problem:
        print(f"\nProblem: {problem}")
    print("\n" + CHAIN_OF_THOUGHT_PROMPT)
    return CHAIN_OF_THOUGHT_PROMPT


def tree_of_thoughts(problem: str = None):
    """Apply Tree of Thoughts exploration."""
    print("🧠 Advanced Reasoning - Tree of Thoughts")
    print("=" * 50)
    if problem:
        print(f"\nProblem: {problem}")
    print("\n" + TREE_OF_THOUGHTS_PROMPT)
    return TREE_OF_THOUGHTS_PROMPT


def mcts_reasoning(problem: str = None):
    """Apply MCTS decision making."""
    print("🧠 Advanced Reasoning - MCTS")
    print("=" * 50)
    if problem:
        print(f"\nProblem: {problem}")
    print("\n" + MCTS_PROMPT)
    return MCTS_PROMPT


def decompose(problem: str = None):
    """Decompose complex problem."""
    print("🧠 Advanced Reasoning - Decomposition")
    print("=" * 50)
    if problem:
        print(f"\nProblem: {problem}")
    print("\n" + DECOMPOSITION_PROMPT)
    return DECOMPOSITION_PROMPT


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Advanced Reasoning - Systematic Problem Solving")
    parser.add_argument("method", choices=["cot", "tot", "mcts", "decompose"], help="Reasoning method")
    parser.add_argument("--problem", "-p", help="Problem to solve")

    args = parser.parse_args()

    if args.method == "cot":
        chain_of_thought(args.problem)
    elif args.method == "tot":
        tree_of_thoughts(args.problem)
    elif args.method == "mcts":
        mcts_reasoning(args.problem)
    elif args.method == "decompose":
        decompose(args.problem)


if __name__ == "__main__":
    main()

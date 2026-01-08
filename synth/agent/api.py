"""
Python API for the True AI Agent.

Provides a clean, programmatic interface for interacting with the agent.
This is the recommended way to integrate the agent into Python applications.
"""

from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import pandas as pd

from synth.agent.true_ai_agent import TrueAIAgent
from synth.agent.models.core import Response, Request, RequestType


class SynthAgent:
    """
    High-level Python API for the SYNTH AI Agent.

    This API provides simple methods for common operations while
    exposing the full agent capabilities when needed.

    Example:
        ```python
        from synth.agent.api import SynthAgent

        # Initialize agent
        agent = SynthAgent()

        # Generate synthetic data
        data = agent.generate(count=1000)

        # Analyze existing data
        insights = agent.analyze(data=df)

        # Validate synthetic data
        validation = agent.validate(synthetic_data=synthetic_df, original_data=original_df)
        ```
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        llm_provider: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the SYNTH Agent.

        Args:
            storage_path: Path for persistent memory storage (default: .agent_memory)
            llm_provider: LLM provider to use (default: from config or first available)
            verbose: Enable verbose output
        """
        self.storage_path = storage_path or ".agent_memory"
        self.verbose = verbose

        # Initialize the underlying agent
        self._agent = TrueAIAgent(
            storage_path=self.storage_path,
            llm_provider=llm_provider,
        )
        self._agent.initialize()

    def generate(
        self,
        count: int = 1000,
        distribution: str = "statistical",
        output_path: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Generate synthetic data.

        Args:
            count: Number of records to generate
            distribution: Distribution strategy ("statistical", "uniform", "clustered")
            output_path: Optional path to save generated data
            **kwargs: Additional parameters for generation

        Returns:
            pandas.DataFrame with generated synthetic data

        Example:
            ```python
            # Generate 1000 records
            data = agent.generate(count=1000)

            # Generate with specific distribution
            data = agent.generate(count=5000, distribution="clustered")

            # Generate and save to file
            data = agent.generate(count=1000, output_path="output.csv")
            ```
        """
        if self.verbose:
            print(f"Generating {count} synthetic records...")

        # Build request
        request_text = f"Generate {count} synthetic records"
        if distribution != "statistical":
            request_text += f" using {distribution} distribution"

        if output_path:
            request_text += f" and export to {output_path}"

        # Add any additional parameters
        if kwargs:
            params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            request_text += f" with {params_str}"

        # Create request
        request = Request(
            request_type=RequestType.GENERATE,
            text=request_text,
            entities={
                "count": count,
                "distribution": distribution,
                "output_path": output_path,
                **kwargs
            }
        )

        # Process request
        import asyncio
        response = asyncio.run(self._agent.process_request(request))

        # Extract and return data
        if response.success and response.data is not None:
            if self.verbose:
                print(f"✓ Generated {len(response.data)} records")
                if response.metadata:
                    time = response.metadata.get("processing_time_seconds", 0)
                    print(f"  Processing time: {time:.2f}s")

            return response.data
        else:
            raise RuntimeError(f"Generation failed: {response.message}")

    def analyze(
        self,
        data: Union[pd.DataFrame, str, Path],
        focus: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze data and provide insights.

        Args:
            data: DataFrame to analyze, or path to data file
            focus: Optional list of analysis focus areas (e.g., ["patterns", "outliers"])
            **kwargs: Additional parameters for analysis

        Returns:
            Dictionary containing analysis results and insights

        Example:
            ```python
            # Analyze a DataFrame
            insights = agent.analyze(data=df)

            # Analyze with specific focus
            insights = agent.analyze(data=df, focus=["patterns", "correlations"])

            # Analyze file
            insights = agent.analyze(data="data.csv")
            ```
        """
        if self.verbose:
            print("Analyzing data...")

        # Load data if path provided
        if isinstance(data, (str, Path)):
            data_path = str(data)
            if data_path.endswith(".csv"):
                df = pd.read_csv(data_path)
            elif data_path.endswith((".xls", ".xlsx")):
                df = pd.read_excel(data_path)
            else:
                raise ValueError(f"Unsupported file format: {data_path}")
        else:
            df = data

        # Build request
        request_text = f"Analyze the data with {len(df)} records and {len(df.columns)} columns"
        if focus:
            request_text += f", focusing on {', '.join(focus)}"

        # Create request
        request = Request(
            request_type=RequestType.ANALYZE,
            text=request_text,
            entities={
                "data": df,
                "focus": focus or [],
                **kwargs
            }
        )

        # Process request
        import asyncio
        response = asyncio.run(self._agent.process_request(request))

        # Extract and return insights
        if response.success:
            if self.verbose:
                print(f"✓ Analysis complete")
                if response.suggestions:
                    print(f"  Found {len(response.suggestions)} suggestions")

            return {
                "message": response.message,
                "insights": response.metadata or {},
                "suggestions": [
                    {
                        "title": s.title,
                        "description": s.description,
                        "benefit": s.benefit
                    }
                    for s in (response.suggestions or [])
                ],
                "warnings": [
                    {
                        "message": w.message,
                        "severity": w.severity.value,
                        "mitigation": w.mitigation
                    }
                    for w in (response.warnings or [])
                ]
            }
        else:
            raise RuntimeError(f"Analysis failed: {response.message}")

    def validate(
        self,
        synthetic_data: Union[pd.DataFrame, str, Path],
        original_data: Optional[Union[pd.DataFrame, str, Path]] = None,
        threshold: float = 0.8,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Validate synthetic data quality.

        Args:
            synthetic_data: Synthetic data to validate, or path to file
            original_data: Original data for comparison (optional)
            threshold: Quality threshold (0-1)
            **kwargs: Additional parameters for validation

        Returns:
            Dictionary containing validation results

        Example:
            ```python
            # Validate against original
            result = agent.validate(
                synthetic_data=synthetic_df,
                original_data=original_df
            )

            # Validate standalone
            result = agent.validate(synthetic_data=synthetic_df)

            # Validate with custom threshold
            result = agent.validate(
                synthetic_data=synthetic_df,
                original_data=original_df,
                threshold=0.9
            )
            ```
        """
        if self.verbose:
            print("Validating synthetic data...")

        # Load data if paths provided
        if isinstance(synthetic_data, (str, Path)):
            synthetic_path = str(synthetic_data)
            if synthetic_path.endswith(".csv"):
                syn_df = pd.read_csv(synthetic_path)
            elif synthetic_path.endswith((".xls", ".xlsx")):
                syn_df = pd.read_excel(synthetic_path)
            else:
                raise ValueError(f"Unsupported file format: {synthetic_path}")
        else:
            syn_df = synthetic_data

        orig_df = None
        if original_data is not None:
            if isinstance(original_data, (str, Path)):
                orig_path = str(original_data)
                if orig_path.endswith(".csv"):
                    orig_df = pd.read_csv(orig_path)
                elif orig_path.endswith((".xls", ".xlsx")):
                    orig_df = pd.read_excel(orig_path)
                else:
                    raise ValueError(f"Unsupported file format: {orig_path}")
            else:
                orig_df = original_data

        # Build request
        request_text = f"Validate synthetic data ({len(syn_df)} records)"
        if orig_df is not None:
            request_text += f" against original data ({len(orig_df)} records)"
        request_text += f" with threshold {threshold}"

        # Create request
        request = Request(
            request_type=RequestType.VALIDATE,
            text=request_text,
            entities={
                "synthetic_data": syn_df,
                "original_data": orig_df,
                "threshold": threshold,
                **kwargs
            }
        )

        # Process request
        import asyncio
        response = asyncio.run(self._agent.process_request(request))

        # Extract and return results
        if response.success:
            if self.verbose:
                print(f"✓ Validation complete")

            return {
                "message": response.message,
                "quality_score": response.metadata.get("quality_score", 0.0) if response.metadata else 0.0,
                "passed": response.metadata.get("passed", False) if response.metadata else False,
                "details": response.metadata or {},
                "warnings": [
                    {
                        "message": w.message,
                        "severity": w.severity.value,
                        "mitigation": w.mitigation
                    }
                    for w in (response.warnings or [])
                ]
            }
        else:
            raise RuntimeError(f"Validation failed: {response.message}")

    def optimize(
        self,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get optimization suggestions for parameters.

        Args:
            context: Optional context information
            **kwargs: Current parameters to optimize

        Returns:
            Dictionary containing optimization suggestions

        Example:
            ```python
            # Get optimization suggestions
            suggestions = agent.optimize(
                count=10000,
                distribution="uniform"
            )

            # Apply suggested values
            optimized_count = suggestions["optimized_parameters"]["count"]
            ```
        """
        if self.verbose:
            print("Analyzing parameters for optimization...")

        # Build request
        request_text = "Optimize the following parameters: "
        if kwargs:
            params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            request_text += params_str

        # Create request
        request = Request(
            request_type=RequestType.OPTIMIZE,
            text=request_text,
            entities=kwargs or {}
        )

        # Process request
        import asyncio
        response = asyncio.run(self._agent.process_request(request))

        # Extract and return suggestions
        if response.success:
            if self.verbose:
                print(f"✓ Optimization analysis complete")

            return {
                "message": response.message,
                "optimized_parameters": response.metadata.get("optimized_parameters", {}) if response.metadata else {},
                "suggestions": [
                    {
                        "parameter": s.parameter_name,
                        "suggested_value": s.suggested_value,
                        "confidence": s.confidence,
                        "reasoning": s.reasoning,
                        "expected_improvement": s.expected_improvement
                    }
                    for s in (response.suggestions or [])
                ]
            }
        else:
            raise RuntimeError(f"Optimization failed: {response.message}")

    def chat(
        self,
        message: str,
        return_full_response: bool = False
    ) -> Union[str, Response]:
        """
        Send a chat message to the agent.

        This is the most flexible way to interact with the agent,
        allowing natural language requests.

        Args:
            message: Natural language request
            return_full_response: Return full Response object (default: False)

        Returns:
            Agent's response message string or full Response object

        Example:
            ```python
            # Simple chat
            response = agent.chat("Generate 1000 records and export to output.csv")

            # Get full response with metadata
            response = agent.chat(
                "What can you tell me about this data?",
                return_full_response=True
            )
            print(response.metadata)
            print(response.suggestions)
            ```
        """
        # Create request
        request = Request(
            request_type=RequestType.CHAT,
            text=message,
            entities={}
        )

        # Process request
        import asyncio
        response = asyncio.run(self._agent.process_request(request))

        # Return based on preference
        if return_full_response:
            return response
        else:
            if response.success:
                return response.message
            else:
                raise RuntimeError(f"Request failed: {response.message}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information.

        Returns:
            Dictionary containing agent status

        Example:
            ```python
            status = agent.get_status()
            print(f"Requests processed: {status['requests_processed']}")
            print(f"Uptime: {status['uptime_seconds']:.1f}s")
            ```
        """
        return self._agent.get_status()

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary containing memory statistics

        Example:
            ```python
            stats = agent.get_memory_stats()
            print(f"Patterns learned: {stats['patterns_count']}")
            print(f"Strategies learned: {stats['strategies_count']}")
            ```
        """
        status = self._agent.get_status()
        return status.get("memory_stats", {})

    def clear_memory(self):
        """
        Clear agent memory.

        This will reset all learned patterns, strategies, and solutions.

        Example:
            ```python
            agent.clear_memory()
            ```
        """
        import shutil
        if Path(self.storage_path).exists():
            shutil.rmtree(self.storage_path)
        self._agent.initialize()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Cleanup if needed
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"SynthAgent(storage_path='{self.storage_path}')"


# Convenience function for quick usage
def quick_agent(**kwargs) -> SynthAgent:
    """
    Create a SynthAgent with default settings.

    Args:
        **kwargs: Arguments to pass to SynthAgent

    Returns:
        Initialized SynthAgent instance

    Example:
        ```python
        from synth.agent.api import quick_agent

        agent = quick_agent()
        data = agent.generate(count=1000)
        ```
    """
    return SynthAgent(**kwargs)


# Module-level convenience functions
def generate(count: int = 1000, **kwargs) -> pd.DataFrame:
    """
    Quick generate synthetic data.

    Args:
        count: Number of records to generate
        **kwargs: Additional parameters

    Returns:
        DataFrame with generated data

    Example:
        ```python
        from synth.agent.api import generate

        data = generate(count=1000)
        ```
    """
    with SynthAgent() as agent:
        return agent.generate(count=count, **kwargs)


def analyze(data: Union[pd.DataFrame, str], **kwargs) -> Dict[str, Any]:
    """
    Quick analyze data.

    Args:
        data: DataFrame or path to data file
        **kwargs: Additional parameters

    Returns:
        Dictionary with analysis results

    Example:
        ```python
        from synth.agent.api import analyze

        insights = analyze(data="data.csv")
        ```
    """
    with SynthAgent() as agent:
        return agent.analyze(data=data, **kwargs)


def validate(synthetic_data: Union[pd.DataFrame, str], **kwargs) -> Dict[str, Any]:
    """
    Quick validate synthetic data.

    Args:
        synthetic_data: Synthetic data or path to file
        **kwargs: Additional parameters

    Returns:
        Dictionary with validation results

    Example:
        ```python
        from synth.agent.api import validate

        result = validate(synthetic_data="synthetic.csv", original_data="original.csv")
        ```
    """
    with SynthAgent() as agent:
        return agent.validate(synthetic_data=synthetic_data, **kwargs)

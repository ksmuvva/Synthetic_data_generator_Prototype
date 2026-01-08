"""
Adaptive Learning - Online and transfer learning.

Implements:
- Online learning from experience
- Transfer learning between domains
- Meta-learning (learning how to learn)
- Strategy adaptation
- Performance prediction
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import time
import json
from pathlib import Path

from synth.agent.models.core import Context, RequestType, StrategyType


@dataclass
class LearningEpisode:
    """A single learning episode."""
    timestamp: float
    context: Dict[str, Any]
    action: str
    parameters: Dict[str, Any]
    outcome: bool
    reward: float
    duration: float
    quality_metrics: Dict[str, float]


@dataclass
class TransferKnowledge:
    """Knowledge transferred from one domain to another."""
    source_domain: str
    target_domain: str
    knowledge_type: str  # strategy, parameter, pattern
    knowledge: Dict[str, Any]
    transfer_success: float
    confidence: float


@dataclass
class MetaLearningPattern:
    """Meta-learning pattern (learning how to learn)."""
    pattern_type: str
    pattern: Dict[str, Any]
    success_rate: float
    usage_count: int
    last_updated: float


class AdaptiveLearningEngine:
    """
    Adaptive learning engine with online and transfer learning.

    Capabilities:
    - Learn from each interaction (online learning)
    - Transfer knowledge between similar tasks
    - Adapt strategies based on performance
    - Predict optimal parameters
    """

    def __init__(
        self,
        storage_path: str = ".adaptive_learning",
        learning_rate: float = 0.1,
        decay_rate: float = 0.99,
    ):
        """
        Initialize adaptive learning engine.

        Args:
            storage_path: Path for persistent learning storage
            learning_rate: How fast to learn from new experiences
            decay_rate: Rate at which old knowledge decays
        """
        self.storage_path = Path(storage_path)
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate

        # Knowledge stores
        self._episodes: List[LearningEpisode] = []
        self._strategy_performance: Dict[str, Dict[str, float]] = {}
        self._parameter_optimization: Dict[str, List[float]] = {}
        self._transfer_knowledge: List[TransferKnowledge] = []
        self._meta_patterns: List[MetaLearningPattern] = []

        # Domain knowledge for transfer learning
        self._domain_features: Dict[str, Dict[str, Any]] = {}

        # Load existing knowledge
        self._load_knowledge()

    def record_experience(
        self,
        context: Context,
        action: str,
        parameters: Dict[str, Any],
        outcome: bool,
        duration: float,
        quality_metrics: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Record a learning episode (online learning).

        Args:
            context: Execution context
            action: Action taken
            parameters: Parameters used
            outcome: Whether action succeeded
            duration: Time taken
            quality_metrics: Optional quality metrics

        Returns:
            Reward signal (0-1)
        """
        # Calculate reward
        reward = self._calculate_reward(outcome, duration, quality_metrics)

        # Create episode
        episode = LearningEpisode(
            timestamp=time.time(),
            context=self._extract_context_features(context),
            action=action,
            parameters=parameters,
            outcome=outcome,
            reward=reward,
            duration=duration,
            quality_metrics=quality_metrics or {},
        )

        # Store episode
        self._episodes.append(episode)

        # Update strategy performance
        self._update_strategy_performance(episode)

        # Update parameter optimization
        self._update_parameter_knowledge(episode)

        # Decay old knowledge
        self._decay_knowledge()

        # Save knowledge periodically
        if len(self._episodes) % 10 == 0:
            self._save_knowledge()

        return reward

    def _calculate_reward(
        self,
        outcome: bool,
        duration: float,
        quality_metrics: Optional[Dict[str, float]],
    ) -> float:
        """Calculate reward for an episode."""
        reward = 0.0

        # Base reward for success/failure
        if outcome:
            reward += 0.7
        else:
            reward -= 0.5

        # Duration bonus (faster is better)
        if duration < 5:
            reward += 0.3
        elif duration < 10:
            reward += 0.2
        elif duration < 30:
            reward += 0.1

        # Quality metrics
        if quality_metrics:
            quality = quality_metrics.get("overall_quality", quality_metrics.get("quality", 0.5))
            reward += (quality - 0.5) * 0.4

        return max(0.0, min(1.0, reward))

    def _extract_context_features(self, context: Context) -> Dict[str, Any]:
        """Extract features from context for learning."""
        features = {
            "request_type": context.request.request_type.value,
            "data_size": len(context.working_variables.get("data", [])),
            "memory_available": context.environment.available_memory_mb,
            "has_constraints": len(context.request.constraints) > 0,
        }

        # Add domain features
        domain = self._identify_domain(context)
        features["domain"] = domain
        self._update_domain_features(domain, context)

        return features

    def _identify_domain(self, context: Context) -> str:
        """Identify the domain of the current task."""
        request_type = context.request.request_type
        data_size = len(context.working_variables.get("data", []))

        # Domain classification
        if request_type == RequestType.DATA_GENERATION:
            if data_size < 100:
                return "small_data_generation"
            elif data_size < 10000:
                return "medium_data_generation"
            else:
                return "large_data_generation"
        elif request_type == RequestType.DATA_VALIDATION:
            return "data_validation"
        elif request_type == RequestType.DATA_ANALYSIS:
            return "data_analysis"
        else:
            return "general"

    def _update_domain_features(self, domain: str, context: Context):
        """Update domain-specific features."""
        if domain not in self._domain_features:
            self._domain_features[domain] = {
                "count": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "common_strategies": {},
            }

        self._domain_features[domain]["count"] += 1

    def _update_strategy_performance(self, episode: LearningEpisode):
        """Update strategy performance metrics."""
        strategy = episode.parameters.get("strategy", "default")
        action = episode.action

        key = f"{action}_{strategy}"
        if key not in self._strategy_performance:
            self._strategy_performance[key] = {
                "success_count": 0,
                "total_count": 0,
                "total_reward": 0.0,
                "avg_duration": 0.0,
            }

        perf = self._strategy_performance[key]
        perf["total_count"] += 1
        if episode.outcome:
            perf["success_count"] += 1
        perf["total_reward"] += episode.reward

        # Update average duration
        old_avg = perf["avg_duration"]
        perf["avg_duration"] = (
            (old_avg * (perf["total_count"] - 1) + episode.duration)
            / perf["total_count"]
        )

    def _update_parameter_knowledge(self, episode: LearningEpisode):
        """Update knowledge about parameter effectiveness."""
        for param_name, param_value in episode.parameters.items():
            if param_name not in self._parameter_optimization:
                self._parameter_optimization[param_name] = []

            # Store value with reward
            self._parameter_optimization[param_name].append({
                "value": param_value,
                "reward": episode.reward,
                "timestamp": episode.timestamp,
            })

            # Keep only recent values
            if len(self._parameter_optimization[param_name]) > 100:
                self._parameter_optimization[param_name] = (
                    self._parameter_optimization[param_name][-100:]
                )

    def _decay_knowledge(self):
        """Apply decay to old knowledge."""
        # Decay strategy performance weights
        for perf in self._strategy_performance.values():
            perf["total_reward"] *= self.decay_rate

    def predict_best_strategy(
        self,
        context: Context,
        action: str,
    ) -> Tuple[str, float]:
        """
        Predict best strategy for given context.

        Args:
            context: Current context
            action: Action to perform

        Returns:
            Tuple of (strategy_name, confidence)
        """
        domain = self._identify_domain(context)

        # Check for transfer learning opportunities
        transferred = self._apply_transfer_learning(domain, action)
        if transferred:
            return transferred

        # Find best strategy from performance history
        best_strategy = "default"
        best_score = -1

        for key, perf in self._strategy_performance.items():
            if key.startswith(action):
                # Calculate score
                if perf["total_count"] > 0:
                    success_rate = perf["success_count"] / perf["total_count"]
                    avg_reward = perf["total_reward"] / perf["total_count"]
                    score = (success_rate * 0.6 + avg_reward * 0.4)

                    if score > best_score:
                        best_score = score
                        best_strategy = key.split("_", 1)[1]

        confidence = min(best_score + 0.5, 1.0) if best_score > -1 else 0.5

        return best_strategy, confidence

    def optimize_parameters(
        self,
        context: Context,
        action: str,
    ) -> Dict[str, Any]:
        """
        Suggest optimized parameters based on learning.

        Args:
            context: Current context
            action: Action to perform

        Returns:
            Optimized parameters
        """
        optimized = {}

        # Use transfer learning if available
        domain = self._identify_domain(context)
        transferred_params = self._get_transferred_parameters(domain, action)
        optimized.update(transferred_params)

        # Optimize based on history
        for param_name, history in self._parameter_optimization.items():
            if len(history) > 5:
                # Calculate weighted average (recent = higher weight)
                total_weight = 0
                weighted_sum = 0

                for i, entry in enumerate(reversed(history[-20:])):
                    weight = (i + 1) / len(history[-20:])
                    weighted_sum += entry["value"] * entry["reward"] * weight
                    total_weight += entry["reward"] * weight

                if total_weight > 0:
                    optimized[param_name] = weighted_sum / total_weight

        return optimized

    def _apply_transfer_learning(
        self,
        target_domain: str,
        action: str,
    ) -> Optional[Tuple[str, float]]:
        """Apply transfer learning from similar domains."""
        # Find similar domains
        similar_domains = self._find_similar_domains(target_domain)

        for source_domain in similar_domains:
            # Check if we have good performance in source domain
            source_key = f"{action}_{source_domain}"
            if source_key in self._strategy_performance:
                perf = self._strategy_performance[source_key]
                if perf["total_count"] > 3:
                    success_rate = perf["success_count"] / perf["total_count"]
                    if success_rate > 0.7:
                        # Transfer knowledge
                        strategy = source_key.split("_", 1)[1]
                        confidence = success_rate * 0.7  # Reduce confidence for transfer

                        # Record transfer
                        self._transfer_knowledge.append(TransferKnowledge(
                            source_domain=source_domain,
                            target_domain=target_domain,
                            knowledge_type="strategy",
                            knowledge={"strategy": strategy},
                            transfer_success=success_rate,
                            confidence=confidence,
                        ))

                        return (strategy, confidence)

        return None

    def _find_similar_domains(self, target_domain: str) -> List[str]:
        """Find domains similar to target domain."""
        similar = []

        # Simple similarity based on domain name
        for domain in self._domain_features.keys():
            if domain != target_domain:
                # Check if domains share base type
                target_base = "_".join(target_domain.split("_")[:-1]) if "_" in target_domain else target_domain
                domain_base = "_".join(domain.split("_")[:-1]) if "_" in domain else domain

                if target_base == domain_base:
                    similar.append(domain)

        return similar

    def _get_transferred_parameters(
        self,
        domain: str,
        action: str,
    ) -> Dict[str, Any]:
        """Get parameters transferred from similar domains."""
        params = {}

        for transfer in self._transfer_knowledge:
            if transfer.target_domain == domain and transfer.knowledge_type == "parameter":
                params.update(transfer.knowledge)

        return params

    def get_meta_learning_insights(self) -> List[Dict[str, Any]]:
        """Get insights from meta-learning."""
        insights = []

        # Strategy effectiveness patterns
        strategy_insights = {}
        for key, perf in self._strategy_performance.items():
            if perf["total_count"] > 5:
                success_rate = perf["success_count"] / perf["total_count"]
                action, strategy = key.split("_", 1)

                if action not in strategy_insights:
                    strategy_insights[action] = {"best": None, "worst": None}

                if strategy_insights[action]["best"] is None or success_rate > strategy_insights[action]["best_rate"]:
                    strategy_insights[action]["best"] = strategy
                    strategy_insights[action]["best_rate"] = success_rate

        for action, insight in strategy_insights.items():
            insights.append({
                "pattern": f"Best strategy for {action}",
                "insight": f"Use '{insight['best']}' for {action}",
                "success_rate": insight["best_rate"],
                "confidence": 0.8,
            })

        # Parameter optimization patterns
        for param_name, history in self._parameter_optimization.items():
            if len(history) > 10:
                # Find optimal range
                values = [h["value"] for h in history if isinstance(h["value"], (int, float))]
                if values:
                    insights.append({
                        "pattern": f"Optimal {param_name}",
                        "insight": f"{param_name} works best around {sum(values)/len(values):.2f}",
                        "confidence": 0.7,
                    })

        return insights

    def learn_from_mistake(
        self,
        error: Exception,
        context: Context,
        action: str,
        parameters: Dict[str, Any],
    ):
        """Learn from a mistake (negative reinforcement)."""
        # Record negative experience
        self.record_experience(
            context=context,
            action=action,
            parameters=parameters,
            outcome=False,
            duration=0,
            quality_metrics={"error": str(error)},
        )

        # Create meta-learning pattern
        error_type = type(error).__name__
        pattern = MetaLearningPattern(
            pattern_type="error_avoidance",
            pattern={
                "error_type": error_type,
                "action": action,
                "problematic_params": parameters,
            },
            success_rate=0.0,
            usage_count=1,
            last_updated=time.time(),
        )

        self._meta_patterns.append(pattern)

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning progress."""
        total_episodes = len(self._episodes)

        if total_episodes == 0:
            return {
                "total_episodes": 0,
                "message": "No learning episodes yet",
            }

        # Calculate overall stats
        recent_episodes = self._episodes[-100:]
        success_rate = sum(1 for e in recent_episodes if e.outcome) / len(recent_episodes)
        avg_reward = sum(e.reward for e in recent_episodes) / len(recent_episodes)

        return {
            "total_episodes": total_episodes,
            "recent_success_rate": success_rate,
            "recent_avg_reward": avg_reward,
            "strategies_learned": len(self._strategy_performance),
            "parameters_optimized": len(self._parameter_optimization),
            "transfers_performed": len(self._transfer_knowledge),
            "meta_patterns": len(self._meta_patterns),
            "domains_discovered": len(self._domain_features),
        }

    def _save_knowledge(self):
        """Save learned knowledge to disk."""
        self.storage_path.mkdir(parents=True, exist_ok=True)

        knowledge = {
            "strategy_performance": self._strategy_performance,
            "parameter_optimization": self._parameter_optimization,
            "domain_features": self._domain_features,
            "meta_patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "pattern": p.pattern,
                    "success_rate": p.success_rate,
                    "usage_count": p.usage_count,
                    "last_updated": p.last_updated,
                }
                for p in self._meta_patterns
            ],
        }

        knowledge_file = self.storage_path / "knowledge.json"
        with open(knowledge_file, "w") as f:
            json.dump(knowledge, f, indent=2)

    def _load_knowledge(self):
        """Load learned knowledge from disk."""
        knowledge_file = self.storage_path / "knowledge.json"

        if knowledge_file.exists():
            try:
                with open(knowledge_file, "r") as f:
                    knowledge = json.load(f)

                self._strategy_performance = knowledge.get("strategy_performance", {})
                self._parameter_optimization = knowledge.get("parameter_optimization", {})
                self._domain_features = knowledge.get("domain_features", {})

                # Reconstruct meta patterns
                for p_data in knowledge.get("meta_patterns", []):
                    self._meta_patterns.append(MetaLearningPattern(**p_data))

            except Exception as e:
                print(f"Error loading knowledge: {e}")

    def get_transfer_learning_opportunities(self) -> List[Dict[str, Any]]:
        """Get opportunities for transfer learning."""
        opportunities = []

        # Find domains with good performance
        high_perf_domains = []
        for domain, features in self._domain_features.items():
            if features.get("success_rate", 0) > 0.7:
                high_perf_domains.append(domain)

        # Find low-performance domains that could benefit
        for domain, features in self._domain_features.items():
            if features.get("success_rate", 1.0) < 0.6:
                for good_domain in high_perf_domains:
                    if self._domains_similar(domain, good_domain):
                        opportunities.append({
                            "source": good_domain,
                            "target": domain,
                            "potential_gain": features.get("success_rate", 0),
                            "confidence": 0.7,
                        })

        return opportunities

    def _domains_similar(self, domain1: str, domain2: str) -> bool:
        """Check if two domains are similar."""
        # Simple similarity check
        parts1 = domain1.split("_")
        parts2 = domain2.split("_")

        # Same base type?
        return parts1[0] == parts2[0] if parts1 and parts2 else False

"""
Long-term persistent memory for the AI Agent.

Stores information across sessions including:
- User preferences
- Learned patterns
- Strategy effectiveness
- Error solutions
- Interaction history
"""

import json
import threading
from pathlib import Path
from typing import Optional, List, Any, Dict
from datetime import datetime


class LongTermMemory:
    """
    Long-term persistent memory.

    Stores:
    - User preferences
    - Learned patterns
    - Strategy effectiveness
    - Error solutions
    - Interaction history
    """

    def __init__(self, storage_path: str = ".agent_memory"):
        """
        Initialize long-term memory.

        Args:
            storage_path: Directory for storing memory files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        # Initialize storage
        self._init_storage()

    def _init_storage(self):
        """Initialize storage backend."""
        # Use JSON files for simplicity
        self._preferences_file = self.storage_path / "preferences.json"
        self._patterns_file = self.storage_path / "patterns.json"
        self._strategies_file = self.storage_path / "strategies.json"
        self._errors_file = self.storage_path / "errors.json"
        self._interactions_file = self.storage_path / "interactions.json"

        # Load existing data
        self._preferences = self._load_json(self._preferences_file, {})
        self._patterns = self._load_json(self._patterns_file, {})
        self._strategies = self._load_json(self._strategies_file, {})
        self._errors = self._load_json(self._errors_file, {})
        self._interactions = self._load_json(self._interactions_file, [])

    def _load_json(self, path: Path, default: Any) -> Any:
        """
        Load JSON file or return default.

        Args:
            path: File path
            default: Default value if file doesn't exist

        Returns:
            Loaded data or default
        """
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save_json(self, path: Path, data: Any) -> None:
        """
        Save data to JSON file.

        Args:
            path: File path
            data: Data to save
        """
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    # User Preferences
    def store_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> None:
        """
        Store user preferences.

        Args:
            user_id: User identifier
            preferences: User preferences dictionary
        """
        with self._lock:
            self._preferences[user_id] = {
                "preferences": preferences,
                "updated_at": datetime.now().isoformat(),
            }
            self._save_json(self._preferences_file, self._preferences)

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences.

        Args:
            user_id: User identifier

        Returns:
            User preferences if found, None otherwise
        """
        with self._lock:
            entry = self._preferences.get(user_id)
            return entry["preferences"] if entry else None

    # Pattern Storage
    def store_pattern(
        self, dataset_id: str, field: str, pattern: Dict[str, Any]
    ) -> None:
        """
        Store learned pattern.

        Args:
            dataset_id: Dataset identifier
            field: Field name
            pattern: Pattern dictionary
        """
        with self._lock:
            if dataset_id not in self._patterns:
                self._patterns[dataset_id] = {}
            self._patterns[dataset_id][field] = {
                "pattern": pattern,
                "learned_at": datetime.now().isoformat(),
            }
            self._save_json(self._patterns_file, self._patterns)

    def get_pattern(
        self, dataset_id: str, field: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get stored pattern.

        Args:
            dataset_id: Dataset identifier
            field: Field name

        Returns:
            Pattern if found, None otherwise
        """
        with self._lock:
            entry = self._patterns.get(dataset_id, {}).get(field)
            return entry["pattern"] if entry else None

    def get_all_patterns(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get all patterns for a dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dictionary of field -> pattern
        """
        with self._lock:
            dataset_patterns = self._patterns.get(dataset_id, {})
            return {
                field: entry["pattern"]
                for field, entry in dataset_patterns.items()
            }

    # Strategy Effectiveness
    def record_strategy_outcome(
        self,
        strategy: str,
        context: Dict[str, Any],
        success: bool,
        metrics: Dict[str, float],
    ) -> None:
        """
        Record strategy outcome.

        Args:
            strategy: Strategy name
            context: Execution context
            success: Whether strategy succeeded
            metrics: Performance metrics
        """
        with self._lock:
            if strategy not in self._strategies:
                self._strategies[strategy] = {
                    "uses": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_duration": 0.0,
                    "avg_quality": 0.0,
                    "history": [],
                }

            entry = self._strategies[strategy]
            entry["uses"] += 1
            if success:
                entry["successes"] += 1
            else:
                entry["failures"] += 1
            entry["total_duration"] += metrics.get("duration", 0.0)

            # Update average quality
            n = entry["uses"]
            old_avg = entry["avg_quality"]
            new_quality = metrics.get("quality", 0.0)
            entry["avg_quality"] = (old_avg * (n - 1) + new_quality) / n

            entry["history"].append({
                "context": context,
                "success": success,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
            })

            # Keep only last 100 history entries
            if len(entry["history"]) > 100:
                entry["history"] = entry["history"][-100:]

            self._save_json(self._strategies_file, self._strategies)

    def get_strategy_stats(self, strategy: str) -> Optional[Dict[str, Any]]:
        """
        Get strategy statistics.

        Args:
            strategy: Strategy name

        Returns:
            Strategy statistics if found, None otherwise
        """
        with self._lock:
            return self._strategies.get(strategy)

    def get_best_strategy(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Get best strategy for context.

        Args:
            context: Execution context

        Returns:
            Best strategy name if found, None otherwise
        """
        with self._lock:
            best_strategy = None
            best_score = -1.0

            for strategy, stats in self._strategies.items():
                if stats["uses"] < 3:  # Need minimum samples
                    continue

                # Calculate score: success_rate * quality
                success_rate = stats["successes"] / stats["uses"]
                score = success_rate * stats["avg_quality"]

                if score > best_score:
                    best_score = score
                    best_strategy = strategy

            return best_strategy

    # Error Solutions
    def store_error_solution(
        self, error_type: str, solution: Dict[str, Any]
    ) -> None:
        """
        Store error solution.

        Args:
            error_type: Type of error
            solution: Solution dictionary
        """
        with self._lock:
            if error_type not in self._errors:
                self._errors[error_type] = []

            self._errors[error_type].append({
                "solution": solution,
                "success_count": 0,
                "last_used": None,
                "created_at": datetime.now().isoformat(),
            })

            # Keep only last 10 solutions per error type
            if len(self._errors[error_type]) > 10:
                self._errors[error_type] = self._errors[error_type][-10:]

            self._save_json(self._errors_file, self._errors)

    def get_error_solution(self, error_type: str) -> Optional[Dict[str, Any]]:
        """
        Get solution for error type.

        Args:
            error_type: Type of error

        Returns:
            Best solution if found, None otherwise
        """
        with self._lock:
            solutions = self._errors.get(error_type, [])
            if not solutions:
                return None

            # Return most successful solution
            best = max(solutions, key=lambda s: s["success_count"])
            return best["solution"]

    def record_solution_success(self, error_type: str, solution: Dict[str, Any]) -> None:
        """
        Record that a solution worked.

        Args:
            error_type: Type of error
            solution: Solution that worked
        """
        with self._lock:
            solutions = self._errors.get(error_type, [])
            for sol in solutions:
                if sol["solution"] == solution:
                    sol["success_count"] += 1
                    sol["last_used"] = datetime.now().isoformat()
                    break

            self._save_json(self._errors_file, self._errors)

    # Interaction History
    def record_interaction(
        self, request: str, response: Dict[str, Any], metadata: Dict[str, Any]
    ) -> None:
        """
        Record interaction.

        Args:
            request: User request
            response: Agent response
            metadata: Interaction metadata
        """
        with self._lock:
            self._interactions.append({
                "request": request,
                "response": response,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat(),
            })

            # Keep only last 1000 interactions
            if len(self._interactions) > 1000:
                self._interactions = self._interactions[-1000:]

            self._save_json(self._interactions_file, self._interactions)

    def find_similar_requests(
        self, request: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar past requests.

        Args:
            request: Current request
            max_results: Maximum number of results

        Returns:
            List of similar interactions
        """
        with self._lock:
            # Simple keyword matching (can be improved with embeddings)
            request_words = set(request.lower().split())
            similarities = []

            for interaction in self._interactions:
                past_request = interaction["request"]
                past_words = set(past_request.lower().split())

                # Jaccard similarity
                intersection = request_words & past_words
                union = request_words | past_words
                similarity = len(intersection) / len(union) if union else 0.0

                if similarity > 0.1:  # Minimum threshold
                    similarities.append((similarity, interaction))

            # Sort by similarity and return top N
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [interaction for _, interaction in similarities[:max_results]]

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        with self._lock:
            return {
                "users": len(self._preferences),
                "datasets": len(self._patterns),
                "strategies": len(self._strategies),
                "error_types": len(self._errors),
                "interactions": len(self._interactions),
            }

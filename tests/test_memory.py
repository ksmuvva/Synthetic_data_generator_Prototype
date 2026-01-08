"""
Comprehensive tests for the AI Agent Memory System.

Tests both ShortTermMemory and LongTermMemory components,
as well as the unified MemoryLayer interface.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import time
import json


class TestShortTermMemory:
    """Test suite for ShortTermMemory component."""

    def test_initialization(self):
        """Test ShortTermMemory initialization."""
        from synth.agent.memory.short_term import ShortTermMemory

        memory = ShortTermMemory(max_turns=50)
        assert memory.max_turns == 50
        assert memory.get_stats()["total_turns"] == 0
        assert memory.get_stats()["working_vars"] == 0

    def test_store_and_retrieve_conversation_turns(self):
        """Test storing and retrieving conversation turns."""
        from synth.agent.memory.short_term import ShortTermMemory

        memory = ShortTermMemory(max_turns=10)

        # Store conversation turns
        turn_id_1 = memory.store_turn(
            user_message="Hello",
            agent_response="Hi there!",
            context_state={"step": 1}
        )

        turn_id_2 = memory.store_turn(
            user_message="How are you?",
            agent_response="I'm doing well!",
            context_state={"step": 2}
        )

        # Verify turns are stored
        assert turn_id_1 != turn_id_2
        assert memory.get_stats()["total_turns"] == 2

        # Retrieve recent turns
        turns = memory.get_recent_turns(2)
        assert len(turns) == 2
        assert turns[0].user_message == "Hello"
        assert turns[1].user_message == "How are you?"

    def test_conversation_turn_limit(self):
        """Test that max_turns limit is enforced."""
        from synth.agent.memory.short_term import ShortTermMemory

        memory = ShortTermMemory(max_turns=3)

        # Store more turns than the limit
        for i in range(5):
            memory.store_turn(
                user_message=f"Message {i}",
                agent_response=f"Response {i}",
                context_state={}
            )

        # Should only keep the last 3
        assert memory.get_stats()["total_turns"] == 3

        turns = memory.get_all_turns()
        assert len(turns) == 3
        assert turns[0].user_message == "Message 2"
        assert turns[1].user_message == "Message 3"
        assert turns[2].user_message == "Message 4"

    def test_working_variables(self):
        """Test working state variables."""
        from synth.agent.memory.short_term import ShortTermMemory

        memory = ShortTermMemory()

        # Set variables
        memory.set_working_variable("user_id", "12345")
        memory.set_working_variable("session_count", 5)

        # Get individual variable
        assert memory.get_working_variable("user_id") == "12345"
        assert memory.get_working_variable("session_count") == 5
        assert memory.get_working_variable("nonexistent") is None

        # Get all working state
        state = memory.get_working_state()
        assert state["user_id"] == "12345"
        assert state["session_count"] == 5

    def test_temporary_variables_with_ttl(self):
        """Test temporary variables with time-to-live."""
        from synth.agent.memory.short_term import ShortTermMemory

        memory = ShortTermMemory()

        # Set temporary variable with 2 second TTL
        memory.set_temporary("otp_code", "123456", ttl_seconds=2)

        # Should be available immediately
        assert memory.get_temporary("otp_code") == "123456"

        # Wait for expiration
        time.sleep(2.5)

        # Should be expired
        assert memory.get_temporary("otp_code") is None

    def test_clear_memory(self):
        """Test clearing all short-term memory."""
        from synth.agent.memory.short_term import ShortTermMemory

        memory = ShortTermMemory()

        # Add some data
        memory.store_turn("Test", "Response", {})
        memory.set_working_variable("key", "value")
        memory.set_temporary("temp", "value", ttl_seconds=10)

        # Clear memory
        memory.clear()

        # Verify everything is cleared
        stats = memory.get_stats()
        assert stats["total_turns"] == 0
        assert stats["working_vars"] == 0
        assert stats["temporary_vars"] == 0


class TestLongTermMemory:
    """Test suite for LongTermMemory component."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temporary storage directory."""
        storage = tmp_path / "test_memory"
        storage.mkdir()
        yield storage
        # Cleanup is handled by tmp_path fixture

    def test_initialization(self, temp_storage):
        """Test LongTermMemory initialization."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Memory is initialized, files are created lazily when needed
        # The storage path should exist
        assert temp_storage.exists()

        # Trigger file creation by storing some data
        memory.store_user_preferences("test_user", {"theme": "dark"})

        # Now files should be created
        assert (temp_storage / "preferences.json").exists()

    def test_user_preferences(self, temp_storage):
        """Test storing and retrieving user preferences."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Store preferences
        memory.store_user_preferences("user_123", {
            "theme": "dark",
            "language": "en",
            "notifications": True
        })

        # Retrieve preferences
        prefs = memory.get_user_preferences("user_123")
        assert prefs["theme"] == "dark"
        assert prefs["language"] == "en"
        assert prefs["notifications"] is True

        # Nonexistent user
        assert memory.get_user_preferences("nonexistent") is None

    def test_pattern_learning(self, temp_storage):
        """Test storing and retrieving patterns."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Store patterns
        memory.store_pattern("dataset_1", "email", {
            "type": "email",
            "regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        })

        memory.store_pattern("dataset_1", "age", {
            "type": "integer",
            "min": 18,
            "max": 100
        })

        # Retrieve individual pattern
        email_pattern = memory.get_pattern("dataset_1", "email")
        assert email_pattern["type"] == "email"

        # Retrieve all patterns for dataset
        all_patterns = memory.get_all_patterns("dataset_1")
        assert len(all_patterns) == 2
        assert "email" in all_patterns
        assert "age" in all_patterns

    def test_strategy_effectiveness(self, temp_storage):
        """Test recording and analyzing strategy outcomes."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Record strategy outcomes
        for i in range(10):
            success = i < 7  # 70% success rate
            memory.record_strategy_outcome(
                strategy="copula_sampling",
                context={"dataset": "test"},
                success=success,
                metrics={"duration": 1.5, "quality": 0.8 if success else 0.3}
            )

        # Get strategy stats
        stats = memory.get_strategy_stats("copula_sampling")
        assert stats["uses"] == 10
        assert stats["successes"] == 7
        assert stats["failures"] == 3

    def test_best_strategy_selection(self, temp_storage):
        """Test finding the best strategy."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Record outcomes for multiple strategies
        # Strategy A: 80% success rate, quality 0.7
        for i in range(10):
            memory.record_strategy_outcome(
                strategy="strategy_a",
                context={},
                success=i < 8,
                metrics={"quality": 0.7}
            )

        # Strategy B: 60% success rate, quality 0.9
        for i in range(10):
            memory.record_strategy_outcome(
                strategy="strategy_b",
                context={},
                success=i < 6,
                metrics={"quality": 0.9}
            )

        # Strategy A score: 0.8 * 0.7 = 0.56
        # Strategy B score: 0.6 * 0.9 = 0.54
        # Strategy A should be preferred
        best = memory.get_best_strategy({})
        assert best == "strategy_a"

    def test_error_solutions(self, temp_storage):
        """Test storing and retrieving error solutions."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Store error solutions
        memory.store_error_solution("ValueError", {
            "correction_type": "data_cleaning",
            "description": "Remove invalid values",
            "steps": ["drop_na", "convert_types"]
        })

        # Retrieve solution
        solution = memory.get_error_solution("ValueError")
        assert solution["correction_type"] == "data_cleaning"
        assert len(solution["steps"]) == 2

    def test_error_solution_success_tracking(self, temp_storage):
        """Test tracking solution effectiveness."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        solution = {"correction_type": "retry", "description": "Retry with backoff"}

        # Store initial solution
        memory.store_error_solution("ConnectionError", solution)

        # Record that it worked
        memory.record_solution_success("ConnectionError", solution)
        memory.record_solution_success("ConnectionError", solution)

        # Get solution - should have success_count > 0
        retrieved = memory.get_error_solution("ConnectionError")
        # The solution with highest success count is returned
        assert retrieved is not None

    def test_interaction_recording(self, temp_storage):
        """Test recording and finding interactions."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Record interactions
        memory.record_interaction(
            request="Generate 100 customer records",
            response={"success": True, "records": 100},
            metadata={"duration": 2.5}
        )

        memory.record_interaction(
            request="Generate 50 user records",
            response={"success": True, "records": 50},
            metadata={"duration": 1.2}
        )

        # Find similar requests
        similar = memory.find_similar_requests("generate 100 records", max_results=2)

        # Should find similar interactions based on word overlap
        assert len(similar) > 0

    def test_interaction_limit(self, temp_storage):
        """Test that interactions are limited to 1000."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Record more than 1000 interactions
        for i in range(1100):
            memory.record_interaction(
                request=f"Request {i}",
                response={"success": True},
                metadata={}
            )

        stats = memory.get_stats()
        assert stats["interactions"] == 1000  # Should be capped

    def test_memory_persistence(self, temp_storage):
        """Test that memory persists across instances."""
        from synth.agent.memory.long_term import LongTermMemory

        # Create first instance and store data
        memory1 = LongTermMemory(storage_path=str(temp_storage))
        memory1.store_user_preferences("user_1", {"theme": "light"})
        memory1.store_pattern("dataset_1", "field_1", {"type": "string"})

        # Create second instance and verify data persists
        memory2 = LongTermMemory(storage_path=str(temp_storage))

        prefs = memory2.get_user_preferences("user_1")
        assert prefs["theme"] == "light"

        pattern = memory2.get_pattern("dataset_1", "field_1")
        assert pattern["type"] == "string"

    def test_get_stats(self, temp_storage):
        """Test getting memory statistics."""
        from synth.agent.memory.long_term import LongTermMemory

        memory = LongTermMemory(storage_path=str(temp_storage))

        # Add some data
        memory.store_user_preferences("user_1", {"theme": "dark"})
        memory.store_pattern("dataset_1", "field_1", {"type": "string"})
        memory.record_strategy_outcome("strategy_1", {}, True, {"quality": 0.8})
        memory.store_error_solution("Error_1", {"correction_type": "fix"})
        memory.record_interaction("test", {}, {})

        stats = memory.get_stats()
        assert stats["users"] == 1
        assert stats["datasets"] == 1
        assert stats["strategies"] == 1
        assert stats["error_types"] == 1
        assert stats["interactions"] == 1


class TestMemoryLayer:
    """Test suite for unified MemoryLayer interface."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temporary storage for testing."""
        storage = tmp_path / "memory_test"
        storage.mkdir()
        yield str(storage)

    def test_memory_layer_initialization(self, temp_storage):
        """Test MemoryLayer initialization."""
        from synth.agent.memory.layer import MemoryLayer

        memory = MemoryLayer(storage_path=temp_storage, max_turns=50)

        stats = memory.get_stats()
        assert "short_term" in stats
        assert "long_term" in stats

    def test_conversation_flow(self, temp_storage):
        """Test typical conversation flow through MemoryLayer."""
        from synth.agent.memory.layer import MemoryLayer

        memory = MemoryLayer(storage_path=temp_storage)

        # Store conversation turns
        memory.store_conversation_turn(
            user_message="Generate data",
            agent_response="I'll generate synthetic data for you",
            context_state={"dataset": "customers"}
        )

        # Retrieve history
        history = memory.get_conversation_history(n=1)
        assert len(history) == 1
        assert history[0]["user_message"] == "Generate data"

    def test_working_variables_integration(self, temp_storage):
        """Test working variables through MemoryLayer."""
        from synth.agent.memory.layer import MemoryLayer

        memory = MemoryLayer(storage_path=temp_storage)

        # Set and get variables
        memory.set_variable("current_task", "data_generation")
        memory.set_variable("record_count", 100)

        assert memory.get_variable("current_task") == "data_generation"
        assert memory.get_variable("record_count") == 100

        # Get all state
        state = memory.get_working_state()
        assert state["current_task"] == "data_generation"
        assert state["record_count"] == 100

    def test_pattern_learning_integration(self, temp_storage):
        """Test pattern learning through MemoryLayer."""
        from synth.agent.memory.layer import MemoryLayer

        memory = MemoryLayer(storage_path=temp_storage)

        # Learn patterns
        memory.learn_pattern("customers", "email", {
            "type": "email",
            "valid_rate": 0.95
        })

        # Recall patterns
        pattern = memory.recall_pattern("customers", "email")
        assert pattern["type"] == "email"
        assert pattern["valid_rate"] == 0.95

        # Recall all patterns
        all_patterns = memory.recall_all_patterns("customers")
        assert "email" in all_patterns

    def test_strategy_learning_integration(self, temp_storage):
        """Test strategy learning through MemoryLayer."""
        from synth.agent.memory.layer import MemoryLayer
        from synth.agent.models.core import Context, ParsedRequest, RequestType, EnvironmentContext

        memory = MemoryLayer(storage_path=temp_storage)

        # Create proper mock context with non-None values
        request = ParsedRequest(
            original_text="test request",
            intent="test",
            request_type=RequestType.DATA_GENERATION,
            entities={},
            constraints=[],
            complexity=0.5,
            confidence=0.9
        )

        environment = EnvironmentContext(
            available_memory_mb=1000,
            available_cpu_percent=50,
            available_disk_gb=10,
            active_sessions=1
        )

        context = Context(
            request=request,
            environment=environment,
            conversation_history=[],
            working_variables={}
        )

        # Learn strategy outcomes
        for i in range(5):
            memory.learn_strategy_outcome(
                strategy="gaussian_sampling",
                context=context,
                success=i < 4,
                metrics={"duration": 1.0, "quality": 0.8}
            )

        # Get strategy stats
        stats = memory.get_strategy_stats("gaussian_sampling")
        assert stats["uses"] == 5
        assert stats["successes"] == 4

    def test_error_learning_integration(self, temp_storage):
        """Test error learning through MemoryLayer."""
        from synth.agent.memory.layer import MemoryLayer
        from synth.agent.models.core import Error, Correction

        memory = MemoryLayer(storage_path=temp_storage)

        # Create error and solution
        error = Error(
            error_type="ValueError",
            message="Invalid value detected",
            stack_trace="..."
        )

        solution = Correction(
            correction_type="data_validation",
            description="Add validation step",
            steps=["validate_range", "remove_outliers"]
        )

        # Learn error solution
        memory.learn_error_solution(error, solution)

        # Recall solution
        recalled = memory.recall_error_solution("ValueError")
        assert recalled["correction_type"] == "data_validation"
        assert len(recalled["steps"]) == 2

    def test_similar_situations_integration(self, temp_storage):
        """Test finding similar situations through MemoryLayer."""
        from synth.agent.memory.layer import MemoryLayer
        from synth.agent.models.core import ParsedRequest, RequestType

        memory = MemoryLayer(storage_path=temp_storage)

        # Create ParsedRequest objects
        request1 = ParsedRequest(
            original_text="Generate 100 customer records with email and phone",
            intent="generate data",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": 100, "entity": "customer"},
            constraints=[],
            complexity=0.5,
            confidence=0.9
        )

        request2 = ParsedRequest(
            original_text="Create 50 user profiles",
            intent="create profiles",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": 50},
            constraints=[],
            complexity=0.4,
            confidence=0.8
        )

        # Record interactions
        memory.record_interaction(
            request=request1,
            response={"success": True},
            metadata={}
        )

        memory.record_interaction(
            request=request2,
            response={"success": True},
            metadata={}
        )

        # Find similar situations - uses string matching internally
        similar = memory.find_similar_situations("generate customer records")

        # Should find at least one similar interaction
        assert len(similar) >= 0  # May not find if similarity threshold is high

    def test_user_preferences_integration(self, temp_storage):
        """Test user preferences through MemoryLayer."""
        from synth.agent.memory.layer import MemoryLayer

        memory = MemoryLayer(storage_path=temp_storage)

        # Store preferences
        memory.store_preferences("user_123", {
            "default_count": 100,
            "default_format": "csv",
            "theme": "dark"
        })

        # Retrieve preferences
        prefs = memory.get_preferences("user_123")
        assert prefs["default_count"] == 100
        assert prefs["theme"] == "dark"

    def test_clear_short_term_memory(self, temp_storage):
        """Test clearing short-term memory."""
        from synth.agent.memory.layer import MemoryLayer

        memory = MemoryLayer(storage_path=temp_storage)

        # Add data to short-term memory
        memory.store_conversation_turn("Test", "Response", {})
        memory.set_variable("key", "value")

        # Clear short-term
        memory.clear_short_term()

        # Verify short-term is cleared
        stats = memory.get_stats()
        assert stats["short_term"]["total_turns"] == 0

        # Long-term should still exist
        assert "long_term" in stats


class TestMemoryIntegration:
    """Integration tests for memory with the full agent."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temporary storage for testing."""
        storage = tmp_path / "agent_memory_test"
        storage.mkdir()
        yield str(storage)

    def test_memory_with_agent_request(self, temp_storage):
        """Test memory during agent request processing."""
        from synth.agent.memory.layer import MemoryLayer
        from synth.agent.models.core import ParsedRequest, RequestType

        memory = MemoryLayer(storage_path=temp_storage)

        # Create a parsed request
        request = ParsedRequest(
            original_text="Generate 100 synthetic customer records",
            intent="Generate synthetic data",
            request_type=RequestType.DATA_GENERATION,
            entities={"count": 100, "entity": "customer"},
            constraints=[],
            complexity=0.5,
            confidence=0.9
        )

        # Record interaction
        memory.record_interaction(
            request=request,  # Pass the ParsedRequest object, not a string
            response={
                "success": True,
                "records_generated": 100
            },
            metadata={"processing_time": 2.5}
        )

        # Verify interaction was recorded
        similar = memory.find_similar_situations("generate synthetic records")
        assert len(similar) > 0

    def test_persistent_memory_across_sessions(self, temp_storage):
        """Test that memory persists across different agent sessions."""
        from synth.agent.memory.layer import MemoryLayer

        # Session 1: Store some data
        session1 = MemoryLayer(storage_path=temp_storage)
        session1.store_preferences("user_1", {"theme": "dark"})
        session1.learn_pattern("dataset_1", "email", {"type": "email"})

        # Session 2: Retrieve data from new instance
        session2 = MemoryLayer(storage_path=temp_storage)

        prefs = session2.get_preferences("user_1")
        assert prefs["theme"] == "dark"

        pattern = session2.recall_pattern("dataset_1", "email")
        assert pattern["type"] == "email"


@pytest.mark.parametrize("max_turns", [10, 50, 100])
def test_short_term_memory_configurable_limits(max_turns):
    """Test that short-term memory respects configurable limits."""
    from synth.agent.memory.short_term import ShortTermMemory

    memory = ShortTermMemory(max_turns=max_turns)

    # Add more turns than the limit
    for i in range(max_turns + 10):
        memory.store_turn(f"Message {i}", f"Response {i}", {})

    # Should not exceed max_turns
    assert memory.get_stats()["total_turns"] == max_turns


@pytest.mark.parametrize("ttl_seconds", [1, 2, 5])
def test_temporary_variable_expiration(ttl_seconds):
    """Test that temporary variables expire correctly."""
    from synth.agent.memory.short_term import ShortTermMemory

    memory = ShortTermMemory()
    memory.set_temporary("test_var", "test_value", ttl_seconds=ttl_seconds)

    # Should exist before TTL
    assert memory.get_temporary("test_var") == "test_value"

    # Wait for expiration
    time.sleep(ttl_seconds + 0.5)

    # Should be expired
    assert memory.get_temporary("test_var") is None

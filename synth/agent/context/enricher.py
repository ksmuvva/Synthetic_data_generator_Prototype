"""
Context Enricher - Semantic Understanding.

Enriches context with:
- Semantic embeddings
- Domain knowledge
- Entity relationships
- Temporal patterns
- User behavior patterns
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import re

from synth.agent.models.core import (
    Context,
    ParsedRequest,
    RequestType,
)


class ContextEnricher:
    """
    Enriches context with semantic understanding.

    Adds depth and meaning to raw context through
    semantic analysis and domain knowledge.
    """

    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        enable_semantic_analysis: bool = True,
        enable_domain_knowledge: bool = True,
        enable_pattern_recognition: bool = True,
    ):
        """
        Initialize context enricher.

        Args:
            llm_provider: Optional LLM provider for semantic analysis
            enable_semantic_analysis: Enable semantic embedding analysis
            enable_domain_knowledge: Enable domain knowledge injection
            enable_pattern_recognition: Enable pattern recognition
        """
        self.llm_provider = llm_provider
        self.enable_semantic_analysis = enable_semantic_analysis
        self.enable_domain_knowledge = enable_domain_knowledge
        self.enable_pattern_recognition = enable_pattern_recognition

        # Domain knowledge base
        self._domain_knowledge = self._init_domain_knowledge()

        # Pattern cache
        self._pattern_cache: Dict[str, Any] = {}

    def enrich(
        self,
        context: Context,
    ) -> Context:
        """
        Enrich context with semantic understanding.

        Args:
            context: Base context to enrich

        Returns:
            Enriched context
        """
        # Add semantic embeddings
        if self.enable_semantic_analysis:
            context = self._add_semantic_embeddings(context)

        # Add domain knowledge
        if self.enable_domain_knowledge:
            context = self._inject_domain_knowledge(context)

        # Add pattern insights
        if self.enable_pattern_recognition:
            context = self._recognize_patterns(context)

        # Add relationship mapping
        context = self._map_relationships(context)

        # Add temporal context
        context = self._add_temporal_context(context)

        return context

    def _add_semantic_embeddings(self, context: Context) -> Context:
        """Add semantic embeddings to context."""
        if not self.llm_provider:
            # Simple keyword-based enrichment as fallback
            return self._add_keyword_features(context)

        try:
            # Extract key concepts from request
            concepts = self._extract_concepts(context.request.original_text)

            # Add to working variables
            context.working_variables["semantic_concepts"] = concepts

            # Calculate intent similarity with history
            if context.conversation_history:
                similarities = self._calculate_intent_similarities(context)
                context.working_variables["intent_similarities"] = similarities

        except Exception:
            # Fallback to keyword features
            context = self._add_keyword_features(context)

        return context

    def _add_keyword_features(self, context: Context) -> Context:
        """Add keyword-based features as fallback."""
        text = context.request.original_text.lower()

        # Extract key terms
        keywords = {
            "entity_types": self._extract_entity_types(text),
            "actions": self._extract_actions(text),
            "modifiers": self._extract_modifiers(text),
            "constraints": self._extract_constraints(text),
        }

        context.working_variables["keyword_features"] = keywords

        return context

    def _extract_entity_types(self, text: str) -> List[str]:
        """Extract entity types from text."""
        entity_patterns = {
            "customer": r"customer|client|user",
            "transaction": r"transaction|payment|order",
            "product": r"product|item|good",
            "employee": r"employee|staff|worker",
            "patient": r"patient|subject",
            "student": r"student|learner",
        }

        found = []
        for entity, pattern in entity_patterns.items():
            if re.search(pattern, text):
                found.append(entity)

        return found

    def _extract_actions(self, text: str) -> List[str]:
        """Extract action words from text."""
        action_patterns = {
            "generate": r"generate|create|make|produce",
            "analyze": r"analyze|examine|study|investigate",
            "validate": r"validate|verify|check",
            "export": r"export|save|output",
            "transform": r"transform|convert|modify",
        }

        found = []
        for action, pattern in action_patterns.items():
            if re.search(pattern, text):
                found.append(action)

        return found

    def _extract_modifiers(self, text: str) -> List[str]:
        """Extract modifiers from text."""
        modifiers = []

        modifier_patterns = {
            "quickly": r"quick|fast|rapid",
            "carefully": r"careful|accurate|precise",
            "privately": r"private|anonymous|secure",
            "realistically": r"realistic|accurate|faithful",
        }

        for modifier, pattern in modifier_patterns.items():
            if re.search(pattern, text):
                modifiers.append(modifier)

        return modifiers

    def _extract_constraints(self, text: str) -> List[str]:
        """Extract constraints from text."""
        constraints = []

        # Numeric constraints
        numbers = re.findall(r"\d+", text)
        if numbers:
            constraints.extend([f"count_{n}" for n in numbers])

        # Format constraints
        formats = re.findall(r"(csv|json|yaml|xml|parquet|excel)", text.lower())
        constraints.extend([f"format_{f}" for f in formats])

        return constraints

    def _inject_domain_knowledge(self, context: Context) -> Context:
        """Inject domain-specific knowledge into context."""
        request_type = context.request.request_type
        entity_type = context.request.entities.get("entity_type", "")

        # Get relevant domain knowledge
        knowledge = self._get_domain_knowledge(request_type, entity_type)

        context.working_variables["domain_knowledge"] = knowledge

        return context

    def _get_domain_knowledge(
        self,
        request_type: RequestType,
        entity_type: str,
    ) -> Dict[str, Any]:
        """Get domain knowledge for request type and entity."""
        knowledge = {}

        # Data generation best practices
        if request_type == RequestType.DATA_GENERATION:
            knowledge["best_practices"] = {
                "use_constraints": True,
                "validate_output": True,
                "preserve_correlations": True,
                "respect_privacy": True,
            }

            # Entity-specific knowledge
            if entity_type == "customer":
                knowledge["typical_fields"] = [
                    "customer_id", "name", "email", "phone",
                    "address", "registration_date", "status"
                ]
                knowledge["privacy_considerations"] = [
                    "PII encryption", "GDPR compliance", "data masking"
                ]

            elif entity_type == "transaction":
                knowledge["typical_fields"] = [
                    "transaction_id", "amount", "timestamp",
                    "customer_id", "merchant", "category"
                ]
                knowledge["validation_rules"] = [
                    "amount > 0", "timestamp valid", "currency format"
                ]

        # Data analysis best practices
        elif request_type == RequestType.DATA_ANALYSIS:
            knowledge["analysis_techniques"] = [
                "statistical_summary", "distribution_analysis",
                "correlation_analysis", "outlier_detection"
            ]

        # Data validation best practices
        elif request_type == RequestType.DATA_VALIDATION:
            knowledge["validation_types"] = [
                "schema_validation", "value_validation",
                "referential_integrity", "business_rules"
            ]

        return knowledge

    def _recognize_patterns(self, context: Context) -> Context:
        """Recognize and annotate patterns in context."""
        patterns = {
            "repeated_requests": self._detect_repeated_requests(context),
            "sequential_tasks": self._detect_sequential_tasks(context),
            "refinement_patterns": self._detect_refinement_patterns(context),
            "escalation_patterns": self._detect_escalation_patterns(context),
        }

        context.working_variables["patterns"] = patterns

        return context

    def _detect_repeated_requests(self, context: Context) -> List[Dict]:
        """Detect repeated similar requests."""
        repeated = []

        if not context.conversation_history:
            return repeated

        current_intent = context.request.intent

        for turn in context.conversation_history:
            # Similar intent detection
            if current_intent.lower() in turn.get("user_message", "").lower():
                repeated.append({
                    "turn_id": turn.get("turn_id"),
                    "timestamp": turn.get("timestamp"),
                    "similarity": "intent_match"
                })

        return repeated

    def _detect_sequential_tasks(self, context: Context) -> List[str]:
        """Detect sequential task patterns."""
        sequential = []

        # Look for sequences like: generate -> validate -> export
        recent_intents = [
            turn.get("agent_response", "")[:50]
            for turn in context.conversation_history[-5:]
        ]

        # Check for common sequences
        if "generate" in str(recent_intents) and "validate" in str(recent_intents):
            sequential.append("generate_validate")

        if "validate" in str(recent_intents) and "export" in str(recent_intents):
            sequential.append("validate_export")

        return sequential

    def _detect_refinement_patterns(self, context: Context) -> List[str]:
        """Detect refinement patterns."""
        refinements = []

        refinement_keywords = ["better", "improve", "fix", "adjust", "modify"]

        for turn in context.conversation_history[-3:]:
            message = turn.get("user_message", "").lower()
            if any(keyword in message for keyword in refinement_keywords):
                refinements.append(turn.get("turn_id"))

        return refinements

    def _detect_escalation_patterns(self, context: Context) -> List[str]:
        """Detect escalation patterns (increasing complexity/urgency)."""
        escalations = []

        urgency_keywords = ["urgent", "asap", "immediately", "critical"]
        complexity_keywords = ["complex", "advanced", "sophisticated"]

        text = context.request.original_text.lower()

        if any(keyword in text for keyword in urgency_keywords):
            escalations.append("urgency")

        if any(keyword in text for keyword in complexity_keywords):
            escalations.append("complexity")

        return escalations

    def _map_relationships(self, context: Context) -> Context:
        """Map entity relationships in context."""
        entities = context.request.entities

        relationships = {}

        # Entity-type relationships
        entity_type = entities.get("entity_type", "")
        if entity_type == "customer":
            relationships["related_entities"] = ["orders", "transactions", "addresses"]
        elif entity_type == "transaction":
            relationships["related_entities"] = ["customer", "product", "merchant"]
        elif entity_type == "product":
            relationships["related_entities"] = ["transactions", "inventory", "categories"]

        # Field relationships
        if "source_file" in entities:
            relationships["has_reference_data"] = True

        if "constraints" in entities:
            relationships["has_constraints"] = True

        context.working_variables["relationships"] = relationships

        return context

    def _add_temporal_context(self, context: Context) -> Context:
        """Add temporal context to working variables."""
        now = datetime.now()

        temporal = {
            "current_time": now.isoformat(),
            "day_of_week": now.strftime("%A"),
            "hour": now.hour,
            "is_business_hours": 9 <= now.hour < 17,
            "is_weekend": now.weekday() >= 5,
        }

        # Time since last interaction
        if context.conversation_history:
            last_turn = context.conversation_history[-1]
            try:
                last_time = datetime.fromisoformat(last_turn.get("timestamp", now.isoformat()))
                time_delta = now - last_time
                temporal["time_since_last_interaction"] = {
                    "seconds": time_delta.total_seconds(),
                    "is_continuation": time_delta.total_seconds() < 300,  # 5 minutes
                }
            except Exception:
                temporal["time_since_last_interaction"] = None

        context.working_variables["temporal_context"] = temporal

        return context

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text (LLM-powered if available)."""
        if not self.llm_provider:
            return self._extract_concepts_keyword(text)

        # LLM-based concept extraction would go here
        # For now, fall back to keyword extraction
        return self._extract_concepts_keyword(text)

    def _extract_concepts_keyword(self, text: str) -> List[str]:
        """Extract concepts using keyword matching."""
        concepts = []

        # Domain-specific concept lists
        concept_lists = {
            "data_generation": ["generate", "create", "synthesize", "simulate"],
            "data_quality": ["validate", "verify", "check", "quality"],
            "privacy": ["anonymous", "private", "gdpr", "hipaa", "privacy"],
            "statistics": ["distribution", "correlation", "variance", "mean"],
            "export": ["export", "save", "output", "format"],
        }

        text_lower = text.lower()

        for concept, keywords in concept_lists.items():
            if any(keyword in text_lower for keyword in keywords):
                concepts.append(concept)

        return concepts

    def _calculate_intent_similarities(self, context: Context) -> List[Dict]:
        """Calculate similarities with historical intents."""
        similarities = []

        current_intent = context.request.intent.lower()

        for turn in context.conversation_history:
            user_msg = turn.get("user_message", "").lower()

            # Simple word overlap similarity
            current_words = set(current_intent.split())
            history_words = set(user_msg.split())

            overlap = len(current_words & history_words)
            total = len(current_words | history_words)

            if total > 0:
                similarity_score = overlap / total
                if similarity_score > 0.3:  # Only include meaningful similarities
                    similarities.append({
                        "turn_id": turn.get("turn_id"),
                        "similarity": similarity_score,
                        "matched_concepts": list(current_words & history_words),
                    })

        return similarities

    def _init_domain_knowledge(self) -> Dict[str, Any]:
        """Initialize domain knowledge base."""
        return {
            "data_generation": {
                "common_strategies": ["statistical", "constrained", "copula"],
                "quality_factors": ["accuracy", "diversity", "consistency"],
                "privacy_techniques": ["anonymization", "k_anonymity", "differential_privacy"],
            },
            "data_analysis": {
                "common_techniques": ["descriptive", "diagnostic", "predictive"],
                "visualization_types": ["histogram", "scatter", "box_plot"],
            },
            "data_validation": {
                "validation_levels": ["schema", "value", "business_rule"],
                "common_errors": ["null_values", "outliers", "invalid_format"],
            },
        }

    def get_enrichment_summary(self, context: Context) -> str:
        """
        Get a summary of context enrichment.

        Args:
            context: Enriched context

        Returns:
            Text summary of enrichment
        """
        lines = [
            "=== Context Enrichment Summary ===",
            "",
            "Semantic Features:",
        ]

        if "semantic_concepts" in context.working_variables:
            concepts = context.working_variables["semantic_concepts"]
            lines.append(f"  Concepts: {', '.join(concepts)}")

        if "keyword_features" in context.working_variables:
            keywords = context.working_variables["keyword_features"]
            lines.append(f"  Entity Types: {keywords.get('entity_types', [])}")
            lines.append(f"  Actions: {keywords.get('actions', [])}")

        lines.append("")
        lines.append("Domain Knowledge:")

        if "domain_knowledge" in context.working_variables:
            knowledge = context.working_variables["domain_knowledge"]
            if "best_practices" in knowledge:
                lines.append(f"  Best Practices: {len(knowledge['best_practices'])}")

        lines.append("")
        lines.append("Patterns:")

        if "patterns" in context.working_variables:
            patterns = context.working_variables["patterns"]
            if patterns.get("repeated_requests"):
                lines.append(f"  Repeated Requests: {len(patterns['repeated_requests'])}")
            if patterns.get("sequential_tasks"):
                lines.append(f"  Sequential Tasks: {', '.join(patterns['sequential_tasks'])}")

        return "\n".join(lines)

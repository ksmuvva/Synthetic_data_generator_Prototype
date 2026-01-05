"""
Base template class and template library.

Program of Thoughts:
1. Define base SchemaTemplate class
2. Template library for managing templates
3. Template registration and discovery
4. Template customization methods
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, get_type_hints
from dataclasses import dataclass, field

from synth.agent.state import FieldSpec, Constraint
from synth.patterns.schema import Schema, Field, FieldType


@dataclass
class TemplateField:
    """Field specification in a template."""
    name: str
    data_type: str
    description: str = ""
    unique: bool = False
    nullable: bool = True
    constraints: dict[str, Any] = field(default_factory=dict)
    default_value: Any = None
    generator: Optional[str] = None  # e.g., "uuid", "person_name", "email"


class SchemaTemplate(ABC):
    """
    Base class for schema templates.

    Self-Reflection: Templates provide pre-defined schemas for
    common use cases, reducing the need for users to specify
    every field from scratch.
    """

    # Subclasses should define these
    template_id: str = "base"
    name: str = "Base Template"
    description: str = "Base template class"
    category: str = "general"

    def __init__(self):
        """Initialize the template."""
        self.fields: dict[str, TemplateField] = {}
        self.constraints: list[Constraint] = []
        self._define_fields()

    @abstractmethod
    def _define_fields(self) -> None:
        """Define the fields for this template."""
        pass

    def get_field_names(self) -> list[str]:
        """Get list of field names."""
        return list(self.fields.keys())

    def get_field(self, name: str) -> Optional[TemplateField]:
        """Get a field by name."""
        return self.fields.get(name)

    def add_field(self, field: TemplateField) -> None:
        """Add a field to the template."""
        self.fields[field.name] = field

    def remove_field(self, name: str) -> bool:
        """Remove a field from the template."""
        if name in self.fields:
            del self.fields[name]
            return True
        return False

    def customize_field(self, name: str, **kwargs) -> bool:
        """
        Customize a field's properties.

        Args:
            name: Field name
            **kwargs: Properties to customize (data_type, constraints, etc.)

        Returns:
            True if field was customized, False if not found
        """
        field = self.fields.get(name)
        if not field:
            return False

        for key, value in kwargs.items():
            if hasattr(field, key):
                setattr(field, key, value)
            else:
                field.constraints[key] = value

        return True

    def to_schema(self, row_count: int = 100) -> Schema:
        """
        Convert template to Schema object.

        Args:
            row_count: Number of rows for the schema

        Returns:
            Schema object with template fields
        """
        schema_fields = []

        for template_field in self.fields.values():
            # Convert TemplateField to Field
            field_type = self._map_type(template_field.data_type)

            # Build field statistics
            stats = self._build_field_stats(template_field)

            field = Field(
                name=template_field.name,
                type=field_type,
                nullable=template_field.nullable,
                unique=template_field.unique,
                **stats
            )
            schema_fields.append(field)

        return Schema(
            row_count=row_count,
            fields=schema_fields,
        )

    def _map_type(self, type_str: str) -> FieldType:
        """Map string type to FieldType."""
        type_map = {
            "integer": FieldType.INTEGER,
            "float": FieldType.FLOAT,
            "string": FieldType.STRING,
            "categorical": FieldType.CATEGORICAL,
            "datetime": FieldType.DATETIME,
            "boolean": FieldType.BOOLEAN,
        }
        return type_map.get(type_str.lower(), FieldType.STRING)

    def _build_field_stats(self, field: TemplateField) -> dict[str, Any]:
        """Build field statistics from template field."""
        stats = {}

        if field.data_type == "integer":
            if "range" in field.constraints:
                min_val, max_val = field.constraints["range"]
            else:
                min_val, max_val = 0, 100
            stats["mean"] = (min_val + max_val) / 2
            stats["std"] = (max_val - min_val) / 6
            stats["min_value"] = min_val
            stats["max_value"] = max_val

        elif field.data_type == "float":
            if "range" in field.constraints:
                min_val, max_val = field.constraints["range"]
            else:
                min_val, max_val = 0.0, 1000.0
            stats["mean"] = (min_val + max_val) / 2
            stats["std"] = (max_val - min_val) / 6
            stats["min_value"] = min_val
            stats["max_value"] = max_val

        elif field.data_type == "string":
            stats["min_length"] = field.constraints.get("min_length", 5)
            stats["max_length"] = field.constraints.get("max_length", 30)
            stats["avg_length"] = (stats["min_length"] + stats["max_length"]) / 2

        elif field.data_type == "categorical":
            if "values" in field.constraints:
                values = field.constraints["values"]
                stats["value_counts"] = {v: 1.0/len(values) for v in values}
                stats["mode"] = values[0] if values else None

        return stats

    def summary(self) -> str:
        """Get a summary of the template."""
        lines = [
            f"Template: {self.name} ({self.template_id})",
            f"Category: {self.category}",
            f"Description: {self.description}",
            f"\nFields ({len(self.fields)}):",
        ]
        for field in self.fields.values():
            unique = " [UNIQUE]" if field.unique else ""
            nullable = "" if field.nullable else " [NOT NULL]"
            lines.append(f"  - {field.name}: {field.data_type}{unique}{nullable}")
            if field.description:
                lines.append(f"    {field.description}")

        return "\n".join(lines)


class TemplateLibrary:
    """
    Library of available templates.

    Self-Reflection: Manages template registration, discovery,
    and retrieval. Provides centralized access to all templates.
    """

    def __init__(self):
        """Initialize the template library."""
        self._templates: dict[str, type[SchemaTemplate]] = {}
        self._instances: dict[str, SchemaTemplate] = {}

    def register(self, template_class: type[SchemaTemplate]) -> None:
        """Register a template class."""
        # Create instance to get template_id
        instance = template_class()
        self._templates[instance.template_id] = template_class
        self._instances[instance.template_id] = instance

    def get(self, template_id: str) -> Optional[SchemaTemplate]:
        """Get a template instance by ID."""
        if template_id in self._instances:
            # Return new instance to avoid state sharing
            template_class = self._templates[template_id]
            return template_class()
        return None

    def list_templates(self) -> list[str]:
        """List all available template IDs."""
        return list(self._templates.keys())

    def list_by_category(self, category: str) -> list[str]:
        """List templates in a specific category."""
        return [
            tid for tid, instance in self._instances.items()
            if instance.category == category
        ]

    def search(self, query: str) -> list[str]:
        """Search templates by name or description."""
        query_lower = query.lower()
        return [
            tid for tid, instance in self._instances.items()
            if query_lower in instance.name.lower() or
               query_lower in instance.description.lower() or
               query_lower in tid
        ]

    def get_all_summaries(self) -> dict[str, str]:
        """Get summaries of all templates."""
        return {
            tid: instance.summary()
            for tid, instance in self._instances.items()
        }


# Global template library instance
_global_library: Optional[TemplateLibrary] = None


def get_template_library() -> TemplateLibrary:
    """Get the global template library instance."""
    global _global_library
    if _global_library is None:
        _global_library = TemplateLibrary()
        # Import and register templates
        from synth.agent.templates.financial import FinancialTransactionTemplate
        from synth.agent.templates.ecommerce import ECommerceOrderTemplate
        from synth.agent.templates.user_profile import UserProfileTemplate

        _global_library.register(FinancialTransactionTemplate)
        _global_library.register(ECommerceOrderTemplate)
        _global_library.register(UserProfileTemplate)

    return _global_library

"""
Schema templates for common use cases.

Provides pre-defined schemas for frequently requested data types.
"""

from synth.agent.templates.base import SchemaTemplate, TemplateLibrary
from synth.agent.templates.financial import FinancialTransactionTemplate
from synth.agent.templates.ecommerce import ECommerceOrderTemplate
from synth.agent.templates.user_profile import UserProfileTemplate

__all__ = [
    "SchemaTemplate",
    "TemplateLibrary",
    "FinancialTransactionTemplate",
    "ECommerceOrderTemplate",
    "UserProfileTemplate",
]

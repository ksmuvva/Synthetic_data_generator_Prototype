"""
Generation modules for synth.
"""

from synth.generation.sampler import StatisticalSampler

# Try to import additional modules, but don't fail if they have issues
try:
    from synth.generation.constrained_sampler import (
        ConstraintType,
        Constraint,
        ConstraintSet,
        ConstraintValidator,
        ConstraintEnforcer,
        ConstrainedSampler,
    )
    _has_constrained = True
except ImportError:
    _has_constrained = False

try:
    from synth.generation.copula_sampler import CopulaSampler
    _has_copula = True
except ImportError:
    _has_copula = False

try:
    from synth.generation.relational_sampler import RelationalSampler
    _has_relational = True
except ImportError:
    _has_relational = False

__all__ = ["StatisticalSampler"]

if _has_constrained:
    __all__.extend([
        "ConstrainedSampler",
        "ConstraintType",
        "Constraint",
        "ConstraintSet",
        "ConstraintValidator",
        "ConstraintEnforcer",
    ])

if _has_copula:
    __all__.append("CopulaSampler")

if _has_relational:
    __all__.append("RelationalSampler")

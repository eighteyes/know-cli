"""
Know Tool - Python implementation for efficient graph operations
"""

__version__ = "1.0.0"

from .graph import GraphManager
from .entities import EntityManager
from .cache import GraphCache
from .dependencies import DependencyManager
from .validation import GraphValidator, ContractValidator
from .generators import SpecGenerator
from .llm import LLMManager, LLMProvider, MockProvider
from .async_graph import AsyncGraphManager, AsyncGraphPool, get_graph
from .diff import GraphDiff
from .feature_tracker import FeatureTracker, create_feature_config
from .contract_manager import ContractManager
from .impact_analyzer import ImpactAnalyzer
from .deprecation import DeprecationManager
from .requirements import RequirementManager
from .coverage import CoverageAnalyzer
from .utils import (
    parse_entity_id,
    format_entity_id,
    normalize_entity_type,
    validate_name_format,
    get_graph_stats
)

__all__ = [
    "GraphManager",
    "EntityManager",
    "GraphCache",
    "DependencyManager",
    "GraphValidator",
    "ContractValidator",
    "SpecGenerator",
    "LLMManager",
    "LLMProvider",
    "MockProvider",
    "AsyncGraphManager",
    "AsyncGraphPool",
    "get_graph",
    "GraphDiff",
    "FeatureTracker",
    "create_feature_config",
    "ContractManager",
    "ImpactAnalyzer",
    "DeprecationManager",
    "RequirementManager",
    "CoverageAnalyzer",
    "parse_entity_id",
    "format_entity_id",
    "normalize_entity_type",
    "validate_name_format",
    "get_graph_stats"
]
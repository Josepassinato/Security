"""Quarry Plugin SDK for Python."""

from .plugin import QuarryPlugin, PluginManifest, PluginContext, PluginResult
from .enricher import EnricherPlugin, EnrichmentRequest, EnrichmentResult
from .action import ActionPlugin, ActionRequest, ActionResult
from .connector import ConnectorPlugin, ConnectorConfig
from .decorators import enricher, action, connector
from .registry import PluginRegistry
from .client import QuarryClient, QuarryClientError
from .loader import load_manifest, load_plugin_from_directory, PluginLoadError

__version__ = "0.1.0"

__all__ = [
    # Core
    "QuarryPlugin",
    "PluginManifest",
    "PluginContext",
    "PluginResult",
    # Enricher
    "EnricherPlugin",
    "EnrichmentRequest",
    "EnrichmentResult",
    # Action
    "ActionPlugin",
    "ActionRequest",
    "ActionResult",
    # Connector
    "ConnectorPlugin",
    "ConnectorConfig",
    # Decorators
    "enricher",
    "action",
    "connector",
    # Registry
    "PluginRegistry",
    # Client
    "QuarryClient",
    "QuarryClientError",
    # Loader
    "load_manifest",
    "load_plugin_from_directory",
    "PluginLoadError",
]

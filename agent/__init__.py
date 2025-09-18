from .registry import registry
from .base import BaseAgent
from .loader import load_agents

# Load all agents when the package is imported
load_agents()

__all__ = ['registry', 'BaseAgent']
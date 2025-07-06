from typing import Dict, Optional
from .base import BaseAgent

class AgentRegistry:
    """Registry for all available agents."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, name: str, agent: BaseAgent) -> None:
        """
        Register an agent with the registry.
        
        Args:
            name: The name of the agent
            agent: The agent instance
        """
        self._agents[name.lower()] = agent
        print(f"Agent '{name}' registered successfully")
    
    def get(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            name: The name of the agent
            
        Returns:
            BaseAgent: The agent instance or None if not found
        """
        return self._agents.get(name.lower())
    
    def list_agents(self) -> Dict[str, BaseAgent]:
        """
        Get all registered agents.
        
        Returns:
            Dict: A dictionary of agent names to agent instances
        """
        return self._agents.copy()

# Create a singleton instance
registry = AgentRegistry()
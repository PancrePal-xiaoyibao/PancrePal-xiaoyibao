from typing import Dict, Optional
from .base import BaseAgent

class AgentRegistry:
    """
    智能体注册表类，用于管理所有可用的智能体（Agent）。

    该类提供注册、获取和列出智能体的方法，实现对智能体实例的集中管理。
    """

    def __init__(self):
        """
        初始化注册表，创建一个用于存储智能体实例的字典。
        """
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        """
        注册一个智能体到注册表中。

        参数:
            name (str): 智能体名称
            agent (BaseAgent): 智能体实例
        """
        self._agents[name.lower()] = agent
        print(f"Agent '{name}' registered successfully")

    def get(self, name: str) -> Optional[BaseAgent]:
        """
        根据名称获取已注册的智能体。

        参数:
            name (str): 智能体名称

        返回:
            Optional[BaseAgent]: 智能体实例，如果未找到则返回 None
        """
        return self._agents.get(name.lower())

    def list_agents(self) -> Dict[str, BaseAgent]:
        """
        获取所有已注册的智能体。

        返回:
            Dict[str, BaseAgent]: 智能体名称到实例的字典副本
        """
        return self._agents.copy()

# 创建单例注册表实例，供全局使用
registry = AgentRegistry()
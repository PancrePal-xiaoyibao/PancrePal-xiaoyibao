from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """Base class that all agents must implement."""
    
    @abstractmethod
    def validate_request(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate if the request data is valid for this agent.
        
        Args:
            request_data: The request data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def process_request(self, request_data: Dict[str, Any]) -> Any:
        """
        Process the request and return response.
        
        Args:
            request_data: The request data to process
            
        Returns:
            Any: The raw response data
        """
        pass
    
    @abstractmethod
    def format_response(self, response_data: Any) -> Dict[str, Any]:
        """
        Format the raw response into a standardized format.
        
        Args:
            response_data: The raw response data
            
        Returns:
            Dict: The formatted response
        """
        pass
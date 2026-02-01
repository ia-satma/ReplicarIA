"""
Tool Registry for ReplicarIA Agents.
Provides a mechanism to register, discover, and invoke tools.
"""

import logging
import inspect
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolRegistry:
    """Registry for agent tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        
    def register(self, name: str, description: str, parameters: Dict[str, Any]):
        """Decorator to register a tool."""
        def decorator(func: Callable):
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                func=func
            )
            logger.info(f"Registered tool: {name}")
            return func
        return decorator
        
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
        
    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())
        
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format."""
        return [t.to_openai_schema() for t in self._tools.values()]
        
    async def invoke(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke a tool by name with arguments."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
            
        try:
            logger.info(f"Invoking tool {name} with args: {json.dumps(arguments)}")
            result = tool.func(**arguments)
            if inspect.iscoroutine(result):
                result = await result
            return result
        except Exception as e:
            logger.error(f"Error invoking tool {name}: {e}")
            return {"error": str(e)}


# Global registry instance
registry = ToolRegistry()


def tool(name: str, description: str, parameters: Dict[str, Any] = None):
    """Decorator alias for registry.register."""
    if parameters is None:
        parameters = {"type": "object", "properties": {}, "required": []}
    return registry.register(name, description, parameters)

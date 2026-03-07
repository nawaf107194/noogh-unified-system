from dataclasses import dataclass
from typing import Dict, Type, Optional, Any

@dataclass
class ComponentConfig:
    """Configuration for components managed by ComponentManager."""
    name: str
    component_type: Type
    args: tuple = ()
    kwargs: dict = {}

class ComponentManager:
    """Registry pattern implementation for managing system components."""
    
    _components: Dict[str, Any] = {}
    _configs: Dict[str, ComponentConfig] = {}
    
    @classmethod
    def register(cls, name: str, component_type: Type, *args, **kwargs) -> None:
        """Register a component with its configuration."""
        cls._configs[name] = ComponentConfig(name, component_type, args, kwargs)
        
    @classmethod
    def unregister(cls, name: str) -> None:
        """Unregister a component."""
        if name in cls._configs:
            del cls._configs[name]
            if name in cls._components:
                del cls._components[name]
                
    @classmethod
    def get_component(cls, name: str) -> Optional[Any]:
        """Retrieve a component instance by name."""
        if name not in cls._components:
            if name not in cls._configs:
                raise ValueError(f"Component {name} not registered.")
            config = cls._configs[name]
            instance = config.component_type(*config.args, **config.kwargs)
            cls._components[name] = instance
        return cls._components[name]
    
    @classmethod
    def get_all_components(cls) -> Dict[str, Any]:
        """Return all registered components."""
        return cls._components.copy()
    
    @classmethod
    def clear_components(cls) -> None:
        """Clear all component instances."""
        cls._components.clear()
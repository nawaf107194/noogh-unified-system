"""
System Registry - سجل المكونات المركزي
Central Component Registry for NOOGH Integration

يوفر إدارة مركزية لجميع مكونات النظام مع دعم:
- Singleton management
- Dependency injection
- Lifecycle management
- Component discovery

Version: 1.0
Author: NOOGH Integration Team
"""

import logging
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("unified_core.integration.registry")

T = TypeVar('T')


class ComponentStatus(Enum):
    """حالة المكون"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class ComponentMetadata:
    """
    معلومات المكون
    Component metadata
    """
    name: str
    component_type: Type
    instance: Any
    status: ComponentStatus
    dependencies: List[str]
    registered_at: float
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.component_type.__name__,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "registered_at": self.registered_at,
            "error": self.error
        }


class SystemRegistry:
    """
    سجل المكونات المركزي
    Central system component registry

    Features:
    - Component registration and retrieval
    - Singleton pattern enforcement
    - Dependency injection
    - Lazy initialization
    - Component lifecycle management
    """

    def __init__(self):
        self._components: Dict[str, ComponentMetadata] = {}
        self._factories: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}  # alias -> real_name

        logger.info("SystemRegistry initialized")

    def register(
        self,
        name: str,
        instance: Any,
        dependencies: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None
    ):
        """
        تسجيل مكون في السجل
        Register a component in the registry

        Args:
            name: اسم المكون (مثل "world_model")
            instance: instance المكون
            dependencies: قائمة بأسماء المكونات التي يعتمد عليها
            aliases: أسماء بديلة للمكون
        """
        import time

        if name in self._components:
            logger.warning(f"Component {name} already registered, replacing")

        metadata = ComponentMetadata(
            name=name,
            component_type=type(instance),
            instance=instance,
            status=ComponentStatus.READY,
            dependencies=dependencies or [],
            registered_at=time.time()
        )

        self._components[name] = metadata

        # تسجيل الأسماء البديلة
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name

        logger.info(
            f"✓ Component registered: {name} ({type(instance).__name__}) "
            f"with {len(dependencies or [])} dependencies"
        )

        # نشر حدث التسجيل
        self._publish_registration_event(name, metadata)

    def register_factory(
        self,
        name: str,
        factory: Callable,
        dependencies: Optional[List[str]] = None
    ):
        """
        تسجيل factory للتهيئة الكسولة
        Register a factory for lazy initialization

        Args:
            name: اسم المكون
            factory: دالة تُنشئ instance المكون
            dependencies: اعتماديات المكون
        """
        import time

        self._factories[name] = factory

        metadata = ComponentMetadata(
            name=name,
            component_type=type(factory),
            instance=None,
            status=ComponentStatus.UNINITIALIZED,
            dependencies=dependencies or [],
            registered_at=time.time()
        )

        self._components[name] = metadata

        logger.info(f"✓ Factory registered: {name}")

    def get(self, name: str, default: Any = None) -> Optional[Any]:
        """
        الحصول على مكون
        Get a component

        Args:
            name: اسم المكون أو alias
            default: القيمة الافتراضية إذا لم يُعثر على المكون

        Returns:
            instance المكون أو default
        """
        # تحويل alias إلى اسم حقيقي
        real_name = self._aliases.get(name, name)

        if real_name not in self._components:
            if default is not None:
                return default
            raise KeyError(f"Component '{name}' not found in registry")

        metadata = self._components[real_name]

        # تهيئة كسولة إذا لزم الأمر
        if metadata.status == ComponentStatus.UNINITIALIZED:
            self._initialize_component(real_name)

        if metadata.status != ComponentStatus.READY:
            logger.warning(
                f"Component {real_name} is not ready (status={metadata.status.value})"
            )

        return metadata.instance

    def _initialize_component(self, name: str):
        """
        تهيئة مكون كسول
        Initialize a lazy component
        """
        metadata = self._components[name]

        if metadata.status != ComponentStatus.UNINITIALIZED:
            return

        metadata.status = ComponentStatus.INITIALIZING
        logger.info(f"Initializing component: {name}")

        try:
            # تحقق من الاعتماديات
            self._check_dependencies(name, metadata.dependencies)

            # استدعاء factory
            factory = self._factories.get(name)
            if not factory:
                raise ValueError(f"No factory found for {name}")

            # تمرير الاعتماديات إذا كان factory يقبلها
            sig = inspect.signature(factory)
            if len(sig.parameters) > 0:
                deps = {dep: self.get(dep) for dep in metadata.dependencies}
                instance = factory(**deps)
            else:
                instance = factory()

            metadata.instance = instance
            metadata.status = ComponentStatus.READY

            logger.info(f"✓ Component initialized: {name}")

        except Exception as e:
            metadata.status = ComponentStatus.ERROR
            metadata.error = str(e)
            logger.error(f"✗ Failed to initialize {name}: {e}", exc_info=True)
            raise

    def _check_dependencies(self, name: str, dependencies: List[str]):
        """
        تحقق من توفر الاعتماديات
        Check dependency availability
        """
        for dep in dependencies:
            real_dep = self._aliases.get(dep, dep)
            if real_dep not in self._components:
                raise ValueError(
                    f"Dependency '{dep}' of '{name}' not found in registry"
                )

            dep_metadata = self._components[real_dep]
            if dep_metadata.status == ComponentStatus.UNINITIALIZED:
                # تهيئة الاعتمادية أولاً
                self._initialize_component(real_dep)

            if dep_metadata.status != ComponentStatus.READY:
                raise ValueError(
                    f"Dependency '{dep}' of '{name}' is not ready "
                    f"(status={dep_metadata.status.value})"
                )

    def has(self, name: str) -> bool:
        """
        تحقق من وجود مكون
        Check if component exists
        """
        real_name = self._aliases.get(name, name)
        return real_name in self._components

    def list_components(self) -> List[str]:
        """
        قائمة بجميع المكونات المسجلة
        List all registered components
        """
        return list(self._components.keys())

    def get_metadata(self, name: str) -> Optional[ComponentMetadata]:
        """
        الحصول على معلومات المكون
        Get component metadata
        """
        real_name = self._aliases.get(name, name)
        return self._components.get(real_name)

    def get_statistics(self) -> Dict[str, Any]:
        """
        إحصائيات السجل
        Registry statistics
        """
        status_counts = {}
        for metadata in self._components.values():
            status_counts[metadata.status.value] = \
                status_counts.get(metadata.status.value, 0) + 1

        return {
            "total_components": len(self._components),
            "total_aliases": len(self._aliases),
            "status_distribution": status_counts,
            "components": [
                metadata.to_dict()
                for metadata in self._components.values()
            ]
        }

    def unregister(self, name: str):
        """
        إلغاء تسجيل مكون
        Unregister a component
        """
        real_name = self._aliases.get(name, name)

        if real_name not in self._components:
            logger.warning(f"Component {name} not found, cannot unregister")
            return

        metadata = self._components[real_name]

        # تنظيف
        if metadata.instance and hasattr(metadata.instance, 'close'):
            try:
                metadata.instance.close()
            except Exception as e:
                logger.error(f"Error closing {name}: {e}")

        metadata.status = ComponentStatus.STOPPED

        del self._components[real_name]

        # إزالة aliases
        aliases_to_remove = [
            alias for alias, target in self._aliases.items()
            if target == real_name
        ]
        for alias in aliases_to_remove:
            del self._aliases[alias]

        logger.info(f"Component unregistered: {name}")

    def _publish_registration_event(self, name: str, metadata: ComponentMetadata):
        """نشر حدث تسجيل المكون"""
        try:
            from .event_bus import get_event_bus, StandardEvents, EventPriority

            event_bus = get_event_bus()
            event_bus.publish_sync(
                StandardEvents.COMPONENT_REGISTERED,
                {
                    "component_name": name,
                    "component_type": metadata.component_type.__name__,
                    "dependencies": metadata.dependencies
                },
                "system_registry",
                EventPriority.NORMAL
            )
        except Exception as e:
            logger.debug(f"Could not publish registration event: {e}")

    def inject_dependencies(self, obj: Any):
        """
        حقن الاعتماديات في كائن
        Inject dependencies into an object

        يبحث عن attributes بأسماء مثل _world_model, _neuron_fabric
        ويحقنها تلقائياً من السجل.

        Usage:
            class MyComponent:
                def __init__(self):
                    self._world_model = None
                    self._neuron_fabric = None

            comp = MyComponent()
            registry.inject_dependencies(comp)  # يحقن تلقائياً
        """
        for attr_name in dir(obj):
            if not attr_name.startswith('_'):
                continue

            attr_value = getattr(obj, attr_name, None)
            if attr_value is not None:
                continue

            # استنتاج اسم المكون من اسم attribute
            # _world_model → world_model
            component_name = attr_name.lstrip('_')

            if self.has(component_name):
                component = self.get(component_name)
                setattr(obj, attr_name, component)
                logger.debug(
                    f"Injected {component_name} into {type(obj).__name__}.{attr_name}"
                )


# ============================================================
#  Singleton Instance
# ============================================================

_registry_instance: Optional[SystemRegistry] = None


def get_registry() -> SystemRegistry:
    """
    الحصول على instance وحيد للسجل
    Get singleton registry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SystemRegistry()
    return _registry_instance


# ============================================================
#  Decorators
# ============================================================

def component(
    name: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    aliases: Optional[List[str]] = None
):
    """
    Decorator لتسجيل class كمكون تلقائياً
    Decorator to auto-register a class as a component

    Usage:
        @component("world_model", dependencies=["neuron_fabric"])
        class WorldModel:
            def __init__(self, neuron_fabric):
                self._fabric = neuron_fabric
    """
    def decorator(cls):
        component_name = name or cls.__name__.lower()

        def factory(**deps):
            return cls(**deps)

        registry = get_registry()
        registry.register_factory(component_name, factory, dependencies)

        return cls

    return decorator


# ============================================================
#  Example Usage
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # إنشاء registry
    registry = get_registry()

    # مثال 1: تسجيل مكون مباشرة
    class WorldModel:
        def __init__(self):
            self.beliefs = []

        def add_belief(self, belief):
            self.beliefs.append(belief)

    world_model = WorldModel()
    registry.register("world_model", world_model, aliases=["wm", "beliefs"])

    # الوصول بأسماء مختلفة
    assert registry.get("world_model") is world_model
    assert registry.get("wm") is world_model
    assert registry.get("beliefs") is world_model

    # مثال 2: تسجيل factory للتهيئة الكسولة
    class NeuronFabric:
        def __init__(self, world_model):
            self._world = world_model
            print(f"NeuronFabric initialized with {world_model}")

    def create_neuron_fabric(world_model):
        return NeuronFabric(world_model)

    registry.register_factory(
        "neuron_fabric",
        create_neuron_fabric,
        dependencies=["world_model"]
    )

    # الوصول يهيّء تلقائياً
    fabric = registry.get("neuron_fabric")
    assert isinstance(fabric, NeuronFabric)

    # مثال 3: Dependency injection
    class DecisionScorer:
        def __init__(self):
            self._world_model = None
            self._neuron_fabric = None

    scorer = DecisionScorer()
    registry.inject_dependencies(scorer)

    assert scorer._world_model is world_model
    assert scorer._neuron_fabric is fabric

    # الإحصائيات
    stats = registry.get_statistics()
    print("\n=== Registry Statistics ===")
    print(f"Total components: {stats['total_components']}")
    print(f"Total aliases: {stats['total_aliases']}")
    print(f"Status distribution: {stats['status_distribution']}")

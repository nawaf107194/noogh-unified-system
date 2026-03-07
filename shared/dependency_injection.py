import abc

class IDependencyInjector(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def register_dependency(self, dependency_name, dependency_instance):
        pass

    @abc.abstractmethod
    def get_dependency(self, dependency_name):
        pass

class DependencyInjector(IDependencyInjector):
    def __init__(self):
        self._dependencies = {}

    def register_dependency(self, dependency_name, dependency_instance):
        if not isinstance(dependency_name, str):
            raise ValueError("Dependency name must be a string.")
        self._dependencies[dependency_name] = dependency_instance

    def get_dependency(self, dependency_name):
        if dependency_name not in self._dependencies:
            raise KeyError(f"Dependency '{dependency_name}' not found.")
        return self._dependencies[dependency_name]

# Example usage
if __name__ == "__main__":
    injector = DependencyInjector()
    
    # Register some dependencies
    injector.register_dependency('logger', get_logger())
    injector.register_dependency('cache', CacheUtility())

    # Retrieve dependencies
    logger = injector.get_dependency('logger')
    cache = injector.get_dependency('cache')

    print(logger)
    print(cache)
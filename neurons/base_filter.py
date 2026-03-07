# neurons/base_filter.py

class FilterStrategy:
    """Base class for all filter strategies"""
    def __init__(self, filter_type: str):
        self.filter_type = filter_type

    def process_data(self, data: dict) -> dict:
        """Process input data according to filter strategy"""
        raise NotImplementedError("Subclasses must implement process_data method")

class FilterFactory:
    """Factory class for creating filter instances"""
    def __init__(self):
        self._creators = {}

    def register(self, filter_type: str, creator):
        """Register a new filter type"""
        self._creators[filter_type] = creator

    def create_filter(self, filter_type: str, **kwargs) -> FilterStrategy:
        """Create a filter instance"""
        creator = self._creators.get(filter_type)
        if not creator:
            raise ValueError(f"Filter type '{filter_type}' not registered")
        return creator(**kwargs)

# Example usage in __main__:
if __name__ == '__main__':
    from data_router import DataRouter

    class LongFilter(FilterStrategy):
        def process_data(self, data: dict) -> dict:
            # Implement long filter logic
            return {k: v for k, v in data.items() if v > 100}

    factory = FilterFactory()
    factory.register('long', LongFilter)
    filter_instance = factory.create_filter('long', filter_type='long')
    
    data_router = DataRouter()
    data = data_router.fetch_data()
    filtered_data = filter_instance.process_data(data)
    print(filtered_data)
# tmp_test_data/strategies.py

class StrategyMeta(type):
    """Metaclass for creating strategy classes dynamically"""
    
    def __new__(cls, name, bases, attrs):
        # Create the base strategy class
        strategy_class = super().__new__(cls, name, bases, attrs)
        
        # Generate strategy implementations based on config
        if hasattr(strategy_class, 'STRATEGIES'):
            for strategy_name, strategy_config in strategy_class.STRATEGIES.items():
                # Create new class dynamically
                new_class = type(
                    f"{strategy_class.__name__}{strategy_name}Strategy",
                    (strategy_class,),
                    {
                        "name": strategy_name,
                        "config": strategy_config,
                        "__init__": lambda self: super(new_class, self).__init__()
                    }
                )
                # Add to module namespace
                globals()[new_class.__name__] = new_class
                
        return strategy_class

class BaseStrategy(metaclass=StrategyMeta):
    """Base strategy class with configuration"""
    
    STRATEGIES = {
        # Strategy name: config
        "Default": {
            "param1": 1,
            "param2": 2
        },
        "Advanced": {
            "param1": 3,
            "param2": 4
        }
    }
    
    def __init__(self):
        super().__init__()
        
    def execute(self):
        """Execute strategy logic"""
        raise NotImplementedError
        
# Usage example
if __name__ == '__main__':
    default = DefaultStrategy()
    advanced = AdvancedStrategy()
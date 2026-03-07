# neural_engine/error_handling_decorator.py

def handle_errors(func):
    """
    A decorator to centralize error handling.
    It catches exceptions raised by the decorated function and logs them.
    """
    import logging
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the exception
            logging.error(f"Error occurred in {func.__name__}: {str(e)}")
            # Optionally re-raise the exception if needed
            raise
    
    return wrapper

# Example usage in another file
from neural_engine.error_handling_decorator import handle_errors

@handle_errors
def some_function_that_may_fail():
    # Function logic that may raise an exception
    pass
import logging

class UnifiedErrorHandler:
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
    
    def handle_error(self, error, context=None):
        """
        Handles an error by logging it and optionally including context.
        
        :param error: The error instance to be handled.
        :param context: Additional context information to include in the log.
        """
        # Log the error with the full traceback
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True)
        
        if context:
            self.logger.error(f"Context: {context}")
        
        # Optionally, you can return a formatted error response for APIs
        return {
            "status": "error",
            "message": str(error),
            "details": context if context else {}
        }

# Example usage in an API endpoint
def some_api_endpoint():
    try:
        # Perform some operations that might raise exceptions
        pass
    except Exception as e:
        error_handler = UnifiedErrorHandler()
        return error_handler.handle_error(e, context={"endpoint": "some_api_endpoint"})
from abc import ABC, abstractmethod

class ErrorHandler(ABC):
    @abstractmethod
    def handle(self, error):
        pass

class LoggingErrorHandler(ErrorHandler):
    def handle(self, error):
        print(f"Logging error: {error}")

class AlertingErrorHandler(ErrorHandler):
    def handle(self, error):
        print(f"Sending alert for error: {error}")

class ErrorHandlerFactory:
    @staticmethod
    def get_error_handler(error_type):
        if error_type == 'logging':
            return LoggingErrorHandler()
        elif error_type == 'alerting':
            return AlertingErrorHandler()
        else:
            raise ValueError("Unknown error handler type")

# Example usage
if __name__ == "__main__":
    error = "Something went wrong"
    
    # Using the factory to get an appropriate error handler
    handler = ErrorHandlerFactory.get_error_handler('logging')
    handler.handle(error)
    
    handler = ErrorHandlerFactory.get_error_handler('alerting')
    handler.handle(error)
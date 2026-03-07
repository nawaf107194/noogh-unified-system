# noogh/utils/error_handler.py

class ErrorHandlerFactory:
    @staticmethod
    def get_error_handler(handler_type):
        if handler_type == 'default':
            return DefaultErrorHandler()
        elif handler_type == 'detailed':
            return DetailedErrorHandler()
        else:
            raise ValueError("Invalid error handler type")

class DefaultErrorHandler:
    def handle_error(self, message):
        print(f"Handling default error: {message}")

class DetailedErrorHandler:
    def handle_error(self, message):
        print(f"Handling detailed error with full stack trace: {message}")
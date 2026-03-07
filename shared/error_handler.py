# shared/error_handler.py

import logging

class ErrorHandler:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    def handle_error(self, error, message=None):
        """
        Handle an error by logging it.
        
        :param error: The error instance.
        :param message: Additional message to log with the error.
        """
        if message:
            self.logger.error(f"{message}: {error}")
        else:
            self.logger.error(error)
    
    def raise_and_log(self, error, message=None):
        """
        Raise an error and log it.
        
        :param error: The error instance.
        :param message: Additional message to log with the error.
        """
        self.handle_error(error, message)
        raise error
    
    @staticmethod
    def configure_logger():
        """
        Configure the default logger for the error handler.
        """
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Example usage
if __name__ == "__main__":
    error_handler = ErrorHandler()
    try:
        # Simulate an error
        raise ValueError("This is a simulated error")
    except Exception as e:
        error_handler.raise_and_log(e, "An error occurred during processing")
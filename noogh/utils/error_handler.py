# noogh/utils/error_handler.py

class ErrorHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
            cls._instance.error_log = []
        return cls._instance

    def log_error(self, error_message):
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.error_log.append(f"{timestamp} - {error_message}")
        print(f"Error logged: {error_message}")

    def get_errors(self):
        return self.error_log

# Example usage:
# from noogh.utils.error_handler import ErrorHandler
# error_handler = ErrorHandler()
# error_handler.log_error("An example error occurred.")
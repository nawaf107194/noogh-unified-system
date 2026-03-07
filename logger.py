import logging

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # Initialize the logger with a default configuration
            cls._instance.logger = logging.getLogger('singleton_logger')
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            cls._instance.logger.addHandler(handler)
            cls._instance.logger.setLevel(logging.DEBUG)  # Set your desired default level
        return cls._instance

    def get_logger(self):
        return self._instance.logger

# Usage example
if __name__ == "__main__":
    logger_instance1 = Logger().get_logger()
    logger_instance2 = Logger().get_logger()

    logger_instance1.info("This is an info message")
    logger_instance2.error("This is an error message")

    # Both instances point to the same logger object
    print(logger_instance1 is logger_instance2)  # Should output True
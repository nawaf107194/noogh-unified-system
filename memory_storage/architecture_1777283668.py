class MemoryStorage:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryStorage, cls).__new__(cls)
            # Initialize your storage mechanism here
            cls._instance.data = {}
        return cls._instance

    def save_data(self, key, value):
        try:
            self.data[key] = value
            print(f"Data saved successfully for key: {key}")
        except Exception as e:
            handle_error(e)

    def load_data(self, key):
        try:
            return self.data.get(key, None)
        except Exception as e:
            handle_error(e)

def handle_error(e):
    """Utility function to handle errors consistently."""
    print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    storage = MemoryStorage()
    storage.save_data("test_key", "test_value")
    print(storage.load_data("test_key"))
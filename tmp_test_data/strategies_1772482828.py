# tmp_test_data/strategies.py

def common_logic(data):
    # Extracted common logic here
    processed_data = data.strip() if isinstance(data, str) else data
    return processed_data

class Strategy:
    def __init__(self, name):
        self.name = name

    def execute(self, data):
        processed_data = common_logic(data)
        # Additional logic specific to this strategy
        print(f"Executing {self.name} with processed data: {processed_data}")

if __name__ == '__main__':
    strategy = Strategy("ExampleStrategy")
    strategy.execute("Sample Data")
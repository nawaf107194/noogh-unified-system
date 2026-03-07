import os
import pandas as pd

class BatchProcessingUtility:
    def __init__(self, batch_size=1000):
        self.batch_size = batch_size

    def process_batches(self, file_path, processor_function):
        """
        Process a large dataset in batches.
        
        :param file_path: Path to the dataset file.
        :param processor_function: Function to process each batch of data.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        df = pd.read_csv(file_path, chunksize=self.batch_size)
        
        for batch in df:
            processor_function(batch)
    
    def create_batches(self, data, batch_size=None):
        """
        Create batches from a list or DataFrame.
        
        :param data: List or DataFrame to be batched.
        :param batch_size: Size of each batch. Defaults to the instance's batch size.
        :return: Generator yielding batches.
        """
        if batch_size is None:
            batch_size = self.batch_size
        
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]

# Example usage
def example_processor_function(batch):
    # Process each batch here
    print(f"Processing batch with shape: {batch.shape}")

if __name__ == "__main__":
    utility = BatchProcessingUtility(batch_size=1000)
    utility.process_batches('path/to/large_dataset.csv', example_processor_function)
import os
import pandas as pd

class ChunkedDataLoader:
    """
    Utility class for loading and processing large datasets in chunks.
    
    Parameters:
    -----------
    file_path : str
        Path to the dataset file.
    chunk_size : int
        Number of rows to load at once.
    usecols : list, optional
        List of column names to load from the dataset.
    """

    def __init__(self, file_path, chunk_size=1000, usecols=None):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.usecols = usecols
        self.data_iterator = None

    def load_data(self):
        """
        Load data in chunks and return an iterator.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")
        
        self.data_iterator = pd.read_csv(self.file_path, chunksize=self.chunk_size, usecols=self.usecols)
        return self.data_iterator

    def process_chunk(self, func, *args, **kwargs):
        """
        Process each chunk using the provided function.
        
        Parameters:
        -----------
        func : callable
            Function to apply on each chunk.
        *args : tuple
            Additional arguments to pass to the function.
        **kwargs : dict
            Additional keyword arguments to pass to the function.
        """
        for chunk in self.load_data():
            func(chunk, *args, **kwargs)

def example_usage():
    # Example usage of ChunkedDataLoader
    loader = ChunkedDataLoader('large_dataset.csv', chunk_size=5000, usecols=['col1', 'col2'])
    loader.process_chunk(print)  # Example: print each chunk

if __name__ == "__main__":
    example_usage()
import json
import pandas as pd

class DataAggregator:
    def __init__(self):
        self.data_sources = []

    def add_data_source(self, source):
        """
        Add a new data source.
        
        :param source: A dictionary representing the data source, containing keys 'name', 'data', and 'format'.
        """
        self.data_sources.append(source)

    def aggregate_data(self):
        """
        Aggregate data from all sources into a standardized format.
        
        Returns a DataFrame with aggregated data.
        """
        aggregated_data = []
        for source in self.data_sources:
            if source['format'] == 'json':
                data = self._load_json(source['data'])
            elif source['format'] == 'csv':
                data = self._load_csv(source['data'])
            else:
                raise ValueError(f"Unsupported data format: {source['format']}")
            
            # Standardize data structure
            standardized_data = self._standardize_data(data)
            aggregated_data.extend(standardized_data)
        
        return pd.DataFrame(aggregated_data)

    def _load_json(self, data):
        """
        Load JSON data.
        
        :param data: JSON string or path to JSON file.
        :return: List of dictionaries representing the data.
        """
        try:
            return json.loads(data) if isinstance(data, str) else data
        except json.JSONDecodeError:
            with open(data, 'r') as f:
                return json.load(f)

    def _load_csv(self, data):
        """
        Load CSV data.
        
        :param data: Path to CSV file.
        :return: List of dictionaries representing the data.
        """
        df = pd.read_csv(data)
        return df.to_dict('records')

    def _standardize_data(self, data):
        """
        Standardize the data format.
        
        :param data: List of dictionaries representing the data.
        :return: List of dictionaries with standardized fields.
        """
        standardized_data = []
        for item in data:
            standardized_item = {
                'id': item.get('id'),
                'timestamp': item.get('timestamp', ''),
                'value': item.get('value', ''),
                'source': item.get('source', '')
            }
            standardized_data.append(standardized_item)
        return standardized_data

# Example usage
if __name__ == "__main__":
    aggregator = DataAggregator()
    aggregator.add_data_source({
        'name': 'sensor_data',
        'data': 'sensor_data.json',
        'format': 'json'
    })
    aggregator.add_data_source({
        'name': 'log_data',
        'data': 'log_data.csv',
        'format': 'csv'
    })

    aggregated_df = aggregator.aggregate_data()
    print(aggregated_df)
# strategies.py

class DataRetrievalStrategy:
    def retrieve_data(self):
        raise NotImplementedError("This method should be overridden")

class DBDataRetrievalStrategy(DataRetrievalStrategy):
    def retrieve_data(self):
        # Connect to the real DB and fetch data
        pass

class APIDataRetrievalStrategy(DataRetrievalStrategy):
    def retrieve_data(self):
        # Fetch data from a real API
        pass

class DataRetrievalFactory:
    @staticmethod
    def get_strategy(strategy_type):
        if strategy_type == 'db':
            return DBDataRetrievalStrategy()
        elif strategy_type == 'api':
            return APIDataRetrievalStrategy()
        else:
            raise ValueError("Invalid strategy type")

# Usage example in tmp_test_data/architecture_1771301253.py
if __name__ == '__main__':
    db_strategy = DataRetrievalFactory.get_strategy('db')
    api_strategy = DataRetrievalFactory.get_strategy('api')

    db_data = db_strategy.retrieve_data()
    api_data = api_strategy.retrieve_data()
class ConsoleApplication:
    def __init__(self, database_operations: DatabaseOperations):
        self.database_operations = database_operations

    def run(self):
        # Example usage of the interface
        query = "SELECT * FROM trades"
        data = self.database_operations.fetch_data(query)
        print(data)

# Usage in a test file or example script
if __name__ == '__main__':
    from sqlalchemy import create_engine
    engine = create_engine('postgresql://user:password@localhost/dbname')
    database_operations = RealDatabaseOperations(engine)
    app = ConsoleApplication(database_operations)
    app.run()
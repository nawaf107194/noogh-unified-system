# dashboard/app.py

import sqlite3

class DataAccessLayer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path)

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def insert_data(self, table, data):
        placeholders = ', '.join(['?'] * len(data))
        columns = ', '.join(data.keys())
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        with self.connection.cursor() as cursor:
            cursor.execute(query, list(data.values()))
            self.connection.commit()

# Usage in app.py
class DashboardApp:
    def __init__(self, db_path):
        self.dal = DataAccessLayer(db_path)

    def fetch_data(self, query, params=None):
        return self.dal.execute_query(query, params)

    def add_dataset(self, dataset_data):
        self.dal.insert_data('datasets', dataset_data)
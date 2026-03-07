# unified_core/db/sqlite_migration.py

import sqlite3
from alembic import command, config

class SQLiteMigration:
    def __init__(self, db_path):
        self.db_path = db_path
        self.config_file = 'alembic.ini'

    def upgrade(self):
        config_ini = config.Config(self.config_file)
        config_ini.set_main_option('sqlalchemy.url', f'sqlite:///{self.db_path}')
        command.upgrade(config_ini, 'head')

    def downgrade(self, version=None):
        config_ini = config.Config(self.config_file)
        config_ini.set_main_option('sqlalchemy.url', f'sqlite:///{self.db_path}')
        if version:
            command.downgrade(config_ini, version)
        else:
            command.downgrade(config_ini, '-1')

    def current_version(self):
        config_ini = config.Config(self.config_file)
        config_ini.set_main_option('sqlalchemy.url', f'sqlite:///{self.db_path}')
        return command.get_current_head(config_ini)

# Example usage
if __name__ == '__main__':
    db_migrator = SQLiteMigration('path/to/your/database.db')
    print(f"Current version: {db_migrator.current_version()}")
    db_migrator.upgrade()
    # db_migrator.downgrade(version='0.1.0')
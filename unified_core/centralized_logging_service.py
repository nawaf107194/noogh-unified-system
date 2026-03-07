import json
from datetime import datetime

class CentralizedLoggingService:
    def __init__(self):
        self.logs = []

    def log(self, level, message, source=None):
        """Log a message at a specified level from a specified source."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'source': source if source else 'unknown'
        }
        self.logs.append(log_entry)
        print(f"{timestamp} [{level}] {source}: {message}")

    def get_logs(self):
        """Retrieve all logged messages."""
        return self.logs

    def filter_logs(self, level=None, source=None):
        """Filter logs by level and/or source."""
        filtered_logs = self.logs
        if level:
            filtered_logs = [log for log in filtered_logs if log['level'] == level]
        if source:
            filtered_logs = [log for log in filtered_logs if log['source'] == source]
        return filtered_logs

    def dump_logs(self, filename='logs.json'):
        """Dump all logs to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.logs, f, indent=4)

# Example usage
if __name__ == "__main__":
    logger = CentralizedLoggingService()
    logger.log('INFO', 'System startup', 'noogh')
    logger.log('WARNING', 'Memory usage high', 'memory_storage')
    logger.log('ERROR', 'Failed to connect', 'gateway')

    # Filter and display logs
    info_logs = logger.filter_logs(level='INFO')
    print("Filtered INFO logs:")
    for log in info_logs:
        print(json.dumps(log, indent=4))

    # Dump all logs to a file
    logger.dump_logs()
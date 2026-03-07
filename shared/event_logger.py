import json
from datetime import datetime

class EventLogger:
    def __init__(self, log_file='events.log'):
        self.log_file = log_file

    def log_event(self, event_type, details):
        """
        Logs an event with a timestamp, type, and details.
        
        :param event_type: str, type of event (e.g., 'state_change', 'user_action')
        :param details: dict, details of the event
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

# Example usage
if __name__ == "__main__":
    logger = EventLogger()
    logger.log_event('user_action', {'action': 'login', 'user_id': 123})
    logger.log_event('state_change', {'new_state': 'active', 'entity': 'agent'})
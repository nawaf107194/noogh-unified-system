import os
import json
from datetime import datetime, timedelta

class DataCompaction:
    def __init__(self, ledger_path, beliefs_path, retention_days=30):
        self.ledger_path = ledger_path
        self.beliefs_path = beliefs_path
        self.retention_days = retention_days

    def _get_old_entries(self, entries, cutoff_date):
        return [entry for entry in entries if datetime.fromisoformat(entry['timestamp']) < cutoff_date]

    def compact_ledger(self):
        try:
            with open(self.ledger_path, 'r') as f:
                ledger_entries = json.load(f)
        except FileNotFoundError:
            print("Ledger file not found.")
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        old_entries = self._get_old_entries(ledger_entries, cutoff_date)

        if old_entries:
            # Archive old entries
            archive_filename = f"ledger_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(os.path.join(os.path.dirname(self.ledger_path), archive_filename), 'w') as f:
                json.dump(old_entries, f, indent=2)

            # Remove old entries from the current ledger
            updated_entries = [entry for entry in ledger_entries if entry not in old_entries]
            with open(self.ledger_path, 'w') as f:
                json.dump(updated_entries, f, indent=2)
            print(f"Archived {len(old_entries)} old ledger entries to {archive_filename}")
        else:
            print("No old ledger entries to archive.")

    def compact_beliefs(self):
        try:
            with open(self.beliefs_path, 'r') as f:
                beliefs_entries = json.load(f)
        except FileNotFoundError:
            print("Beliefs file not found.")
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        old_entries = self._get_old_entries(beliefs_entries, cutoff_date)

        if old_entries:
            # Archive old entries
            archive_filename = f"beliefs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(os.path.join(os.path.dirname(self.beliefs_path), archive_filename), 'w') as f:
                json.dump(old_entries, f, indent=2)

            # Remove old entries from the current beliefs
            updated_entries = [entry for entry in beliefs_entries if entry not in old_entries]
            with open(self.beliefs_path, 'w') as f:
                json.dump(updated_entries, f, indent=2)
            print(f"Archived {len(old_entries)} old beliefs entries to {archive_filename}")
        else:
            print("No old beliefs entries to archive.")

if __name__ == "__main__":
    compactor = DataCompaction('path/to/ledger.json', 'path/to/beliefs.json')
    compactor.compact_ledger()
    compactor.compact_beliefs()
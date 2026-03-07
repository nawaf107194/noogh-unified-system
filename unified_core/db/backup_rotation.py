# unified_core/db/backup_rotation.py

from datetime import datetime, timedelta
import os
import shutil

def _build_backup_path(base_path):
    current_date = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(base_path, f"backup_{current_date}.sqlite")

def rotate_backups(backup_folder, max_days=30):
    now = datetime.now()
    for file_name in os.listdir(backup_folder):
        if file_name.startswith("backup_") and file_name.endswith(".sqlite"):
            file_path = os.path.join(backup_folder, file_name)
            file_date = datetime.strptime(file_name.split("_")[1], "%Y-%m-%d")
            if (now - file_date).days > max_days:
                os.remove(file_path)

def backup_database(base_path):
    backup_path = _build_backup_path(base_path)
    shutil.copyfile(os.path.join(base_path, "memory_store.db"), backup_path)
    rotate_backups(base_path)

if __name__ == '__main__':
    base_path = '../path/to/your/data'
    backup_database(base_path)
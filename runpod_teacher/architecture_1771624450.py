# runpod_teacher/utils.py
def load_config(file_path):
    """Load configuration from a file."""
    with open(file_path, 'r') as config_file:
        return config_file.read()

def save_data(data, file_path):
    """Save data to a file."""
    with open(file_path, 'w') as output_file:
        output_file.write(data)
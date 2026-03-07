from pathlib import Path


def require_data_dir(base_dir: str) -> Path:
    """
    Ensure the data directory exists.
    base_dir must be provided from the validated SecretsManager.
    """
    if not base_dir:
        raise RuntimeError("Data directory path is missing in SecretsManager")
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

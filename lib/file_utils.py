import os


def create_nested_directory(path: str) -> None:
    """
    Create a nested directory structure from the given path string.

    Args:
        path (str): The directory path to create. Can be relative or absolute.

    Returns:
        None
    """
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        raise Exception(f"Failed to create directory {path}: {str(e)}")

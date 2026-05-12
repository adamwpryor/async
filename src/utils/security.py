import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def load_secure_key(key_name: str) -> str:
    """Securely loads an API key or secret from environment variables.
    
    Args:
        key_name (str): The name of the environment variable to retrieve.
        
    Returns:
        str: The value of the environment variable.
        
    Raises:
        ValueError: If the environment variable is missing or empty.
    """
    value = os.getenv(key_name)
    if not value:
        raise ValueError(f"Missing required secure key: {key_name}")
    return value

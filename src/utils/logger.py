import logging
import os
from pythonjsonlogger import jsonlogger
import git

def get_git_context():
    """Retrieves current Git commit hash and branch.
    
    Returns:
        dict: A dictionary containing 'git_commit' and 'git_branch'.
    """
    try:
        repo = git.Repo(search_parent_directories=True)
        return {
            "git_commit": repo.head.object.hexsha,
            "git_branch": repo.active_branch.name
        }
    except Exception:
        return {
            "git_commit": "unknown",
            "git_branch": "unknown"
        }

class GitContextFilter(logging.Filter):
    """Filter to inject Git context into log records."""
    def __init__(self):
        super().__init__()
        self.git_context = get_git_context()

    def filter(self, record):
        record.git_commit = self.git_context.get("git_commit")
        record.git_branch = self.git_context.get("git_branch")
        return True

def setup_logger(name: str) -> logging.Logger:
    """Configures and returns a structured JSON logger with Git context.
    
    Args:
        name (str): The name of the logger.
        
    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s %(git_commit)s %(git_branch)s'
        )
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
        logger.addFilter(GitContextFilter())
        
    return logger

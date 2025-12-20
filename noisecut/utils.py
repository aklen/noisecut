"""
Utility functions and constants
"""

import shutil


class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    NC = '\033[0m'  # No Color


def get_terminal_width(default: int = 80) -> int:
    """Get terminal width, with fallback"""
    return shutil.get_terminal_size((default, 20)).columns


def format_location(file_path: str, line: int, column: int) -> str:
    """Format a file location as path:line:column"""
    return f"{file_path}:{line}:{column}"

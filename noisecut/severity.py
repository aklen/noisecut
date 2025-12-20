"""
Warning severity classification
"""

from typing import Optional


class Severity:
    """Warning severity levels"""
    CRITICAL = "CRITICAL"  # Memory corruption, undefined behavior
    HIGH = "HIGH"          # Likely bugs, dangerous patterns
    MEDIUM = "MEDIUM"      # Code quality issues
    LOW = "LOW"            # Style, cosmetic issues
    INFO = "INFO"          # Informational only


# Map of warning categories to severity levels
SEVERITY_MAP = {
    # Critical - Memory/UB issues
    "-Wdelete-incomplete": Severity.CRITICAL,
    "-Wdelete-non-virtual-dtor": Severity.CRITICAL,
    "-Wuninitialized": Severity.CRITICAL,
    "-Wreturn-type": Severity.CRITICAL,
    "-Warray-bounds": Severity.CRITICAL,
    "-Wdangling-pointer": Severity.CRITICAL,
    "-Wuse-after-free": Severity.CRITICAL,
    
    # High - Likely bugs
    "-Wsometimes-uninitialized": Severity.HIGH,
    "-Wmaybe-uninitialized": Severity.HIGH,
    "-Wsign-compare": Severity.HIGH,
    "-Wformat": Severity.HIGH,
    "-Wnull-dereference": Severity.HIGH,
    "-Wdivision-by-zero": Severity.HIGH,
    "-Wshift-overflow": Severity.HIGH,
    
    # Medium - Code quality
    "-Wunused-variable": Severity.MEDIUM,
    "-Wunused-parameter": Severity.MEDIUM,
    "-Wshadow": Severity.MEDIUM,
    "-Wconversion": Severity.MEDIUM,
    "-Wdeprecated": Severity.MEDIUM,
    
    # Low - Style/cosmetic
    "-Winconsistent-missing-override": Severity.LOW,
    "-Wmissing-braces": Severity.LOW,
    "-Wextra-semi": Severity.LOW,
    "-Wcomma": Severity.LOW,
    
    # Info
    "-Wcpp": Severity.INFO,
    "-Wpragmas": Severity.INFO,
}


def get_severity(category: str) -> str:
    """
    Get severity level for a warning category.
    
    Args:
        category: Warning category (e.g., "-Wunused-parameter")
        
    Returns:
        Severity level string
    """
    return SEVERITY_MAP.get(category, Severity.MEDIUM)


def get_severity_color(severity: str) -> str:
    """
    Get ANSI color code for severity level.
    
    Args:
        severity: Severity level
        
    Returns:
        ANSI color code
    """
    from .utils import Color
    
    severity_colors = {
        Severity.CRITICAL: Color.RED + Color.BOLD,
        Severity.HIGH: Color.RED,
        Severity.MEDIUM: Color.YELLOW,
        Severity.LOW: Color.YELLOW + Color.DIM,
        Severity.INFO: Color.CYAN,
    }
    
    return severity_colors.get(severity, Color.YELLOW)

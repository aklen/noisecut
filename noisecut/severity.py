"""
Warning severity classification

Reference for comprehensive warning lists:
- Clang warnings: https://github.com/Barro/compiler-warnings/blob/master/clang/warnings-clang-top-level-8.txt
- GCC warnings: https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html
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
    "-Wdangling": Severity.CRITICAL,
    "-Wdangling-field": Severity.CRITICAL,
    "-Wdangling-initializer-list": Severity.CRITICAL,
    "-Wreturn-stack-address": Severity.CRITICAL,
    "-Wuse-after-free": Severity.CRITICAL,
    "-Winfinite-recursion": Severity.CRITICAL,
    "-Wnull-dereference": Severity.CRITICAL,
    
    # High - Likely bugs
    "-Wsometimes-uninitialized": Severity.HIGH,
    "-Wmaybe-uninitialized": Severity.HIGH,
    "-Wconditional-uninitialized": Severity.HIGH,
    "-Wsign-compare": Severity.HIGH,
    "-Wformat": Severity.HIGH,
    "-Wformat-security": Severity.HIGH,
    "-Wdivision-by-zero": Severity.HIGH,
    "-Wshift-overflow": Severity.HIGH,
    "-Woverflow": Severity.HIGH,
    "-Wunsequenced": Severity.HIGH,
    "-Wfor-loop-analysis": Severity.HIGH,
    "-Wself-assign": Severity.HIGH,
    "-Wself-assign-field": Severity.HIGH,
    "-Wself-move": Severity.HIGH,
    "-Wimplicit-fallthrough": Severity.HIGH,
    "-Wimplicit-function-declaration": Severity.HIGH,
    
    # Medium - Code quality
    "-Wunused-variable": Severity.MEDIUM,
    "-Wunused-parameter": Severity.MEDIUM,
    "-Wunused-function": Severity.MEDIUM,
    "-Wunused-but-set-variable": Severity.MEDIUM,
    "-Wunused-result": Severity.MEDIUM,
    "-Wshadow": Severity.MEDIUM,
    "-Wconversion": Severity.MEDIUM,
    "-Wdeprecated": Severity.MEDIUM,
    "-Wdeprecated-declarations": Severity.MEDIUM,
    "-Wreorder-ctor": Severity.MEDIUM,
    "-Wreorder": Severity.MEDIUM,
    "-Wmacro-redefined": Severity.MEDIUM,
    
    # Low - Style/cosmetic
    "-Winconsistent-missing-override": Severity.LOW,
    "-Wmissing-braces": Severity.LOW,
    "-Wextra-semi": Severity.LOW,
    "-Wcomma": Severity.LOW,
    "-Wpedantic": Severity.LOW,
    "-Wc++20-extensions": Severity.LOW,
    "-Wc++17-extensions": Severity.LOW,
    "-Wc++14-extensions": Severity.LOW,
    
    # Info
    "-Wcpp": Severity.INFO,
    "-Wpragmas": Severity.INFO,
    "-W#warnings": Severity.INFO,
}


def get_severity(category: str) -> str:
    """
    Get severity level for a warning category.
    
    Handles categories with optional values like "-Wimplicit-fallthrough=".
    
    Args:
        category: Warning category (e.g., "-Wunused-parameter" or "-Wimplicit-fallthrough=")
        
    Returns:
        Severity level string
    """
    # Try exact match first
    if category in SEVERITY_MAP:
        return SEVERITY_MAP[category]
    
    # Try without trailing = or =N
    # e.g., "-Wimplicit-fallthrough=" -> "-Wimplicit-fallthrough"
    if '=' in category:
        base_category = category.split('=')[0]
        if base_category in SEVERITY_MAP:
            return SEVERITY_MAP[base_category]
    
    return Severity.MEDIUM


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

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
    
    # .NET/C# Critical - Nullability & Memory Safety
    "-WCS8600": Severity.CRITICAL,  # Converting null literal or possible null value to non-nullable type
    "-WCS8601": Severity.CRITICAL,  # Possible null reference assignment
    "-WCS8602": Severity.CRITICAL,  # Dereference of a possibly null reference
    "-WCS8603": Severity.CRITICAL,  # Possible null reference return
    "-WCS8604": Severity.CRITICAL,  # Possible null reference argument
    "-WCS8605": Severity.CRITICAL,  # Unboxing a possibly null value
    "-WCS8625": Severity.CRITICAL,  # Cannot convert null literal to non-nullable reference type
    "-WCS8618": Severity.CRITICAL,  # Non-nullable field must contain a non-null value when exiting constructor
    
    # .NET High - Likely bugs
    "-WCS0162": Severity.HIGH,      # Unreachable code detected
    "-WCS0219": Severity.HIGH,      # Variable is assigned but its value is never used
    "-WCS0472": Severity.HIGH,      # Result of expression is always the same
    "-WCS1717": Severity.HIGH,      # Assignment made to same variable
    "-WCS8509": Severity.HIGH,      # Switch expression does not handle all possible values
    "-WCS8524": Severity.HIGH,      # Switch expression does not handle some null inputs
    "-WCS8073": Severity.HIGH,      # Result of expression is always the same (nullable)
    
    # .NET Medium - Code quality
    "-WCS0168": Severity.MEDIUM,    # Variable declared but never used
    "-WCS0414": Severity.MEDIUM,    # Field assigned but its value never used
    "-WCS0649": Severity.MEDIUM,    # Field never assigned to, always has default value
    "-WCS0169": Severity.MEDIUM,    # Field is never used
    "-WCS1998": Severity.MEDIUM,    # Async method lacks await operators
    "-WCS8019": Severity.MEDIUM,    # Unnecessary using directive
    "-WCS8632": Severity.MEDIUM,    # Nullable annotation should only be used in code within '#nullable' context
    
    # .NET Low - Obsolete APIs & Style
    "-WSYSLIB0001": Severity.LOW,   # Obsolete: UTF7Encoding
    "-WSYSLIB0011": Severity.LOW,   # Obsolete: BinaryFormatter
    "-WSYSLIB0021": Severity.LOW,   # Obsolete: Derived cryptographic types
    "-WSYSLIB0022": Severity.LOW,   # Obsolete: Rijndael and RijndaelManaged
    "-WSYSLIB0023": Severity.LOW,   # Obsolete: RNGCryptoServiceProvider
    "-WSYSLIB0032": Severity.LOW,   # Obsolete: Recovery from corrupted state exceptions
    "-WSYSLIB0041": Severity.LOW,   # Obsolete: Some Rfc2898DeriveBytes constructors
    "-WSYSLIB0050": Severity.LOW,   # Obsolete: Formatter-based serialization
    "-WSYSLIB0051": Severity.LOW,   # Obsolete: Legacy serialization infrastructure
    "-WSYSLIB0057": Severity.LOW,   # Obsolete: X509Certificate constructors
    "-WCS0618": Severity.LOW,       # Type or member is obsolete
    "-WCS0612": Severity.LOW,       # Type or member is obsolete (no message)
    
    # Code Analysis (CA####)
    "-WCA1031": Severity.MEDIUM,    # Do not catch general exception types
    "-WCA1062": Severity.HIGH,      # Validate arguments of public methods
    "-WCA1304": Severity.MEDIUM,    # Specify CultureInfo
    "-WCA1305": Severity.MEDIUM,    # Specify IFormatProvider
    "-WCA1822": Severity.LOW,       # Mark members as static
    "-WCA2007": Severity.LOW,       # Do not directly await a Task
    
    # Roslyn IDE (IDE####)
    "-WIDE0001": Severity.LOW,      # Simplify names
    "-WIDE0003": Severity.LOW,      # Remove this or Me qualification
    "-WIDE0005": Severity.LOW,      # Remove unnecessary using directives
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

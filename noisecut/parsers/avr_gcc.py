"""
AVR-GCC compiler output parser
"""

from .gcc import GccParser


class AvrGccParser(GccParser):
    """
    Parser for AVR-GCC compiler output.
    
    AVR-GCC uses the same output format as regular GCC,
    so we inherit from GccParser without modifications.
    This class exists for potential future AVR-specific customizations.
    """
    pass

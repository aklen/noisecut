"""
Parser factory and auto-detection
"""

from typing import Optional
from .base import BaseParser
from .gcc import GccParser
from .clang import ClangParser
from .avr_gcc import AvrGccParser


def detect_parser(line: str) -> Optional[str]:
    """
    Detect which parser to use based on a line of compiler output.
    
    Args:
        line: A line from compiler output
        
    Returns:
        Parser name ('gcc', 'clang', 'avr-gcc') or None if not detected
    """
    line_lower = line.lower()
    
    # Check for compiler executable in the line
    if 'avr-gcc' in line_lower or 'avr-g++' in line_lower:
        return 'avr-gcc'
    elif 'clang++' in line_lower or 'clang' in line_lower:
        return 'clang'
    elif 'g++' in line_lower or 'gcc' in line_lower:
        return 'gcc'
    
    return None


def create_parser(parser_type: str) -> BaseParser:
    """
    Create a parser instance based on type.
    
    Args:
        parser_type: One of 'gcc', 'clang', 'avr-gcc', or 'auto'
        
    Returns:
        Parser instance
    """
    if parser_type == 'clang':
        return ClangParser()
    elif parser_type == 'avr-gcc':
        return AvrGccParser()
    elif parser_type == 'gcc':
        return GccParser()
    elif parser_type == 'auto':
        # Return a special parser that auto-detects
        return AutoDetectParser()
    else:
        # Default to GCC
        return GccParser()


class AutoDetectParser(BaseParser):
    """
    Parser that automatically detects the compiler and delegates to the appropriate parser.
    """
    
    def __init__(self):
        super().__init__()
        self._delegate: Optional[BaseParser] = None
        self._parser_type: Optional[str] = None
    
    def parse_line(self, line: str) -> Optional[str]:
        """Parse a line, auto-detecting the compiler if needed."""
        
        # If we haven't detected a parser yet, try to detect it
        if self._delegate is None:
            detected = detect_parser(line)
            if detected:
                self._parser_type = detected
                self._delegate = create_parser(detected)
                # Copy our stats to the delegate
                self._delegate.stats = self.stats
                self._delegate.issues = self.issues
                self._delegate.current_issue = self.current_issue
        
        # If we have a delegate, use it
        if self._delegate:
            result = self._delegate.parse_line(line)
            # Sync state back
            self.stats = self._delegate.stats
            self.issues = self._delegate.issues
            self.current_issue = self._delegate.current_issue
            return result
        
        # No parser detected yet, pass through important lines
        if line.strip():
            if line.startswith('make'):
                from ..utils import Color
                return f"{Color.BOLD}{line}{Color.NC}"
        
        return None
    
    def finalize(self):
        """Finalize parsing."""
        if self._delegate:
            self._delegate.finalize()
            # Sync state back
            self.stats = self._delegate.stats
            self.issues = self._delegate.issues
            self.current_issue = self._delegate.current_issue
        else:
            super().finalize()
    
    @property
    def detected_parser(self) -> Optional[str]:
        """Get the detected parser type."""
        return self._parser_type

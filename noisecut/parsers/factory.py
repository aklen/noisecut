"""
Parser factory and auto-detection
"""

import os
import re
from typing import Optional
from pathlib import Path
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


def detect_from_warning_format(lines: list) -> Optional[str]:
    """
    Try to detect compiler from warning/error format.
    
    Args:
        lines: List of output lines to analyze
        
    Returns:
        Parser name or None
    """
    # Look for compiler-specific warning patterns
    for line in lines:
        # AVR-GCC often has AVR-specific warnings
        if 'avr' in line.lower() and ('warning' in line.lower() or 'error' in line.lower()):
            return 'avr-gcc'
        
        # Clang has specific diagnostic formats
        if re.search(r'\[-W[\w-]+\]', line) and 'clang' in ' '.join(lines).lower():
            return 'clang'
    
    return None


def detect_from_project_files() -> Optional[str]:
    """
    Try to detect compiler from project files (Makefile, CMakeLists.txt, PKGBUILD, etc).
    
    Returns:
        Parser name or None
    """
    cwd = Path.cwd()
    
    # Check Makefile
    makefile_paths = [
        cwd / 'Makefile',
        cwd / 'makefile',
        cwd / 'GNUmakefile'
    ]
    
    for makefile in makefile_paths:
        if makefile.exists():
            try:
                content = makefile.read_text(encoding='utf-8', errors='ignore').lower()
                if 'avr-gcc' in content or 'avr-g++' in content:
                    return 'avr-gcc'
                elif 'clang++' in content or 'clang' in content:
                    return 'clang'
                elif 'gcc' in content or 'g++' in content:
                    return 'gcc'
            except:
                pass
    
    # Check CMakeLists.txt
    cmake_file = cwd / 'CMakeLists.txt'
    if cmake_file.exists():
        try:
            content = cmake_file.read_text(encoding='utf-8', errors='ignore').lower()
            if 'avr-gcc' in content:
                return 'avr-gcc'
            elif 'clang' in content:
                return 'clang'
        except:
            pass
    
    # Check PKGBUILD (Arch Linux package)
    pkgbuild = cwd / 'PKGBUILD'
    if pkgbuild.exists():
        try:
            content = pkgbuild.read_text(encoding='utf-8', errors='ignore').lower()
            if 'avr-gcc' in content or 'avr-g++' in content:
                return 'avr-gcc'
            elif 'clang' in content:
                return 'clang'
        except:
            pass
    
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
    Uses multiple fallback mechanisms:
    1. Direct compiler detection from command lines
    2. Warning/error format analysis
    3. Project file inspection (Makefile, CMakeLists.txt, PKGBUILD)
    4. Default to GCC after threshold
    """
    
    def __init__(self):
        super().__init__()
        self._delegate: Optional[BaseParser] = None
        self._parser_type: Optional[str] = None
        self._lines_checked = 0
        self._buffered_lines = []  # Store lines for format analysis
        self._max_buffer = 100  # Store first 100 lines for analysis
        self._max_lines_to_check = 50  # Try detection for 50 lines before fallback
    
    def parse_line(self, line: str) -> Optional[str]:
        """Parse a line, auto-detecting the compiler if needed."""
        
        # If we haven't detected a parser yet, try to detect it
        if self._delegate is None:
            self._lines_checked += 1
            
            # Buffer lines for potential format analysis
            if len(self._buffered_lines) < self._max_buffer:
                self._buffered_lines.append(line)
            
            # Try direct detection from line
            detected = detect_parser(line)
            if detected:
                self._activate_parser(detected)
            elif self._lines_checked == 10:
                # After 10 lines, try project file detection
                detected = detect_from_project_files()
                if detected:
                    self._activate_parser(detected)
            elif self._lines_checked == 30:
                # After 30 lines, try format analysis
                detected = detect_from_warning_format(self._buffered_lines)
                if detected:
                    self._activate_parser(detected)
            elif self._lines_checked >= self._max_lines_to_check:
                # Default to GCC if we can't detect after many lines
                self._activate_parser('gcc')
        
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
    
    def _activate_parser(self, parser_type: str):
        """Activate a specific parser and replay buffered lines."""
        self._parser_type = parser_type
        self._delegate = create_parser(parser_type)
        
        # Copy our stats to the delegate
        self._delegate.stats = self.stats
        self._delegate.issues = self.issues
        self._delegate.current_issue = self.current_issue
        
        # Replay buffered lines through the new parser
        for buffered_line in self._buffered_lines:
            self._delegate.parse_line(buffered_line)
        
        # Clear buffer to free memory
        self._buffered_lines = []
        
        # Sync state back
        self.stats = self._delegate.stats
        self.issues = self._delegate.issues
        self.current_issue = self._delegate.current_issue
    
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

"""
Parser factory and auto-detection

Uses the compiler registry for streamlined detection and instantiation.
"""

import os
import re
from typing import Optional
from pathlib import Path
from .base import BaseParser
from .registry import (
    get_parser,
    get_compiler_by_keyword,
    get_compiler_by_project_files,
    COMPILER_REGISTRY
)
# Import to trigger registration
from . import builtin


def detect_parser(line: str) -> Optional[str]:
    """
    Detect which parser to use based on a line of compiler output.
    Uses the compiler registry for detection.
    
    Args:
        line: A line from compiler output
        
    Returns:
        Parser name (registry key) or None if not detected
    """
    line_lower = line.lower()
    
    # Check each registered compiler's detection keywords
    for key, metadata in COMPILER_REGISTRY.items():
        # Check command patterns
        for pattern in metadata.command_patterns:
            if pattern in line_lower:
                return key
        
        # Check detection keywords
        for keyword in metadata.detection_keywords:
            if keyword in line_lower:
                return key
    
    # Special format detection for .NET
    if re.search(r'\(\d+,\d+\):\s+(warning|error)\s+[A-Z]{2}\d{4}:', line):
        return 'dotnet'
    
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
        # .NET/MSBuild pattern: file.cs(76,34): warning CS0168:
        if re.search(r'\(\d+,\d+\):\s+(warning|error)\s+[A-Z]{2}\d{4}:', line):
            return 'dotnet'
        
        # AVR-GCC often has AVR-specific warnings
        if 'avr' in line.lower() and ('warning' in line.lower() or 'error' in line.lower()):
            return 'avr-gcc'
        
        # Clang has specific diagnostic formats
        if re.search(r'\[-W[\w-]+\]', line) and 'clang' in ' '.join(lines).lower():
            return 'clang'
    
    return None


def detect_from_project_files() -> Optional[str]:
    """
    Try to detect compiler from project files using the registry.
    
    Returns:
        Parser name or None
    """
    cwd = Path.cwd()
    
    # Collect all project files in current directory
    project_files = []
    
    # Check for specific project files from registry
    for key, metadata in COMPILER_REGISTRY.items():
        for pattern in metadata.project_files:
            # Handle glob patterns
            if '*' in pattern:
                matches = list(cwd.glob(pattern))
                if matches:
                    return key
            else:
                # Direct file check
                if (cwd / pattern).exists():
                    return key
    
    # Check Makefile content for compiler hints
    makefile_paths = [
        cwd / 'Makefile',
        cwd / 'makefile',
        cwd / 'GNUmakefile'
    ]
    
    for makefile in makefile_paths:
        if makefile.exists():
            try:
                content = makefile.read_text(encoding='utf-8', errors='ignore').lower()
                # Check each compiler's detection keywords
                for key, metadata in COMPILER_REGISTRY.items():
                    for keyword in metadata.detection_keywords:
                        if keyword in content:
                            return key
            except:
                pass
    
    return None


def create_parser(parser_type: str) -> BaseParser:
    """
    Create a parser instance based on type.
    Uses the compiler registry for instantiation.
    
    Args:
        parser_type: Compiler key from registry, or 'auto'
        
    Returns:
        Parser instance
    """
    if parser_type == 'auto':
        # Return a special parser that auto-detects
        return AutoDetectParser()
    
    try:
        return get_parser(parser_type)
    except KeyError:
        # Fallback to GCC if unknown compiler
        return get_parser('gcc')


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

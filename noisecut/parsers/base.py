"""
Base parser interface for compiler output
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, List
from pathlib import Path

from ..model import BuildIssue, BuildStats
from ..utils import Color


class BaseParser(ABC):
    """Abstract base class for compiler output parsers"""
    
    def __init__(self):
        self.issues: List[BuildIssue] = []
        self.current_issue: Optional[BuildIssue] = None
        self.stats = BuildStats()
    
    @abstractmethod
    def parse_line(self, line: str) -> Optional[str]:
        """
        Parse a single line of compiler output.
        
        Args:
            line: A line of compiler output
            
        Returns:
            Formatted output line or None if line should be hidden
        """
        pass
    
    def finalize(self):
        """Call when parsing is complete to save any pending issues"""
        if self.current_issue:
            self.issues.append(self.current_issue)
            self.current_issue = None
    
    def _format_compilation(self, source_file: str, output_file: str) -> str:
        """Format a compilation line"""
        source_name = Path(source_file).name
        output_name = Path(output_file).name
        return f"{Color.CYAN}[CC]{Color.NC} {source_name} → {output_name}"
    
    def _format_moc(self, source_file: str, output_file: str) -> str:
        """Format a MOC generation line"""
        source_name = Path(source_file).name
        output_name = Path(output_file).name
        return f"{Color.MAGENTA}[MOC]{Color.NC} {source_name} → {output_name}"

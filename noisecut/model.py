"""
Data models for build output analysis
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class BuildIssue:
    """Represents a compiler warning or error"""
    type: str  # 'warning' or 'error'
    file: str
    line: int
    column: int
    message: str
    detail: str = ""
    category: str = ""  # e.g., [-Wunused-parameter]
    
    def __hash__(self):
        return hash((self.type, self.message, self.category))
    
    def __eq__(self, other):
        if not isinstance(other, BuildIssue):
            return False
        return (self.type == other.type and 
                self.message == other.message and 
                self.category == other.category)


@dataclass
class GroupedIssue:
    """Groups multiple occurrences of the same issue"""
    issue: BuildIssue
    locations: List[Tuple[str, int, int, str]] = field(default_factory=list)  # file, line, col, original_message
    
    @property
    def count(self) -> int:
        return len(self.locations)


@dataclass
class BuildStats:
    """Build statistics"""
    files_compiled: int = 0
    moc_generated: int = 0
    warnings: int = 0
    errors: int = 0
    duration: float = 0.0

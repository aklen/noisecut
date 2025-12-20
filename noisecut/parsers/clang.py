"""
Clang/Clang++ compiler output parser
"""

import re
from typing import Optional

from .base import BaseParser
from ..model import BuildIssue
from ..utils import Color


class ClangParser(BaseParser):
    """Parser for Clang and Clang++ compiler output"""
    
    # Patterns for compiler output
    COMPILE_PATTERN = re.compile(
        r'^\s*(?:.*?/)?(clang\+\+|clang).*?-o\s+(\S+)\s+(\S+)$'
    )
    
    MOC_PATTERN = re.compile(
        r'^\s*(?:.*?/)?moc\s+.*?-o\s+(\S+)\s+(\S+)$'
    )
    
    # Issue patterns (same as GCC)
    ISSUE_PATTERN = re.compile(
        r'^(.*?):(\d+):(\d+):\s+(warning|error):\s+(.+?)(?:\s+\[([-\w]+)\])?$'
    )
    
    NOTE_PATTERN = re.compile(
        r'^(.*?):(\d+):(\d+):\s+note:\s+(.+)$'
    )
    
    DETAIL_PATTERN = re.compile(
        r'^\s+\d+\s+\|'  # Line showing source code context
    )
    
    def parse_line(self, line: str) -> Optional[str]:
        """Parse a single line of Clang output. Returns formatted line or None."""
        
        # Check for compilation
        compile_match = self.COMPILE_PATTERN.match(line)
        if compile_match:
            self.stats.files_compiled += 1
            output_file = compile_match.group(2)
            source_file = compile_match.group(3)
            return self._format_compilation(source_file, output_file)
        
        # Check for MOC
        moc_match = self.MOC_PATTERN.match(line)
        if moc_match:
            self.stats.moc_generated += 1
            output_file = moc_match.group(1)
            source_file = moc_match.group(2)
            return self._format_moc(source_file, output_file)
        
        # Check for warnings/errors
        issue_match = self.ISSUE_PATTERN.match(line)
        if issue_match:
            file_path, line_num, col_num, issue_type, message, category = issue_match.groups()
            
            # Save previous issue
            if self.current_issue:
                self.issues.append(self.current_issue)
            
            # Create new issue
            self.current_issue = BuildIssue(
                type=issue_type,
                file=file_path,
                line=int(line_num),
                column=int(col_num),
                message=message,
                category=category or ""
            )
            
            if issue_type == 'warning':
                self.stats.warnings += 1
            else:
                self.stats.errors += 1
            
            return None  # Will be formatted later when grouped
        
        # Check for notes (additional context)
        note_match = self.NOTE_PATTERN.match(line)
        if note_match and self.current_issue:
            file_path, line_num, col_num, note_text = note_match.groups()
            if not self.current_issue.detail:
                self.current_issue.detail = note_text
            return None
        
        # Check for source code context lines
        if self.DETAIL_PATTERN.match(line):
            return None
        
        # Pass through other lines (make commands, etc.)
        if line.strip():
            if line.startswith('make'):
                return f"{Color.BOLD}{line}{Color.NC}"
            elif 'error' in line.lower() and 'make:' in line.lower():
                return f"{Color.RED}{Color.BOLD}{line}{Color.NC}"
        
        return None

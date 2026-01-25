"""
Rust compiler (rustc/cargo) output parser
"""

import re
from typing import Optional
from pathlib import Path

from .base import BaseParser
from ..model import BuildIssue


class RustParser(BaseParser):
    """Parser for Rust compiler output (rustc, cargo build/test)"""
    
    def __init__(self):
        super().__init__()
        self._pending_issue = None  # Store issue until we get location
    
    # Rust warning/error pattern: "warning: unused variable: `actions`"
    ISSUE_LINE_PATTERN = re.compile(
        r'^\s*(warning|error)(?:\[([^\]]+)\])?\s*:\s*(.+)$'
    )
    
    # Location pattern: "   --> helix-core/src/machine.rs:341:13"
    LOCATION_PATTERN = re.compile(
        r'^\s*-->\s+(.+?):(\d+):(\d+)$'
    )
    
    # Category pattern: "   = note: `#[warn(unused_variables)]` ..."
    CATEGORY_PATTERN = re.compile(
        r'^\s*=\s*(?:note|help|warning):\s*`#\[warn\(([^\)]+)\)\]`'
    )
    
    # Compilation status
    COMPILING_PATTERN = re.compile(
        r'^\s*Compiling\s+(\S+)'
    )
    
    FINISHED_PATTERN = re.compile(
        r'^\s*Finished\s+.*target\(s\)'
    )
    
    def parse_line(self, line: str) -> Optional[str]:
        """Parse a single line of Rust compiler output."""
        
        # Check for compilation status
        compile_match = self.COMPILING_PATTERN.match(line)
        if compile_match:
            self.stats.files_compiled += 1
            crate_name = compile_match.group(1)
            return f"Compiling {crate_name}..."
        
        # Check for issue line (warning/error) - store temporarily
        issue_match = self.ISSUE_LINE_PATTERN.match(line)
        if issue_match:
            issue_type = issue_match.group(1)  # 'warning' or 'error'
            error_code = issue_match.group(2)  # e.g., 'E0616' or None
            message = issue_match.group(3)
            
            # Store as pending until we get location from --> line
            self._pending_issue = {
                'type': issue_type,
                'code': error_code,
                'message': message
            }
            
            if issue_type == 'warning':
                self.stats.warnings += 1
            else:
                self.stats.errors += 1
            
            return None
        
        # Check for location line (creates issue from pending)
        location_match = self.LOCATION_PATTERN.match(line)
        if location_match and self._pending_issue:
            file_path = location_match.group(1)
            line_num = int(location_match.group(2))
            col_num = int(location_match.group(3))
            
            # Save previous issue if any
            if self.current_issue:
                self.issues.append(self.current_issue)
            
            # Create issue with location
            self.current_issue = BuildIssue(
                type=self._pending_issue['type'],
                file=file_path,
                line=line_num,
                column=col_num,
                message=self._pending_issue['message'],
                category=self._pending_issue['code'] or ""
            )
            
            self._pending_issue = None
            return None
        
        # Check for category annotation (adds to current issue)
        category_match = self.CATEGORY_PATTERN.match(line)
        if category_match and self.current_issue:
            # Update category if we found the #[warn(...)] annotation
            category = category_match.group(1)
            if not self.current_issue.category:
                self.current_issue.category = category
            return None
        
        # Check for build finished
        if self.FINISHED_PATTERN.match(line):
            # Flush last issue
            if self.current_issue:
                self.issues.append(self.current_issue)
                self.current_issue = None
            return None
        
        # Pass through other lines
        return None
    
    def finalize(self):
        """Finalize parsing and flush any pending issue."""
        if self.current_issue:
            self.issues.append(self.current_issue)
            self.current_issue = None
    
    @staticmethod
    def detect(lines: list) -> bool:
        """Detect if output is from Rust compiler."""
        rust_keywords = [
            'Compiling',
            'cargo',
            'rustc',
            '-->',
            'error[E',
            '#[warn(',
            'help: if this is intentional'
        ]
        
        text = '\n'.join(lines[:50])
        return any(keyword in text for keyword in rust_keywords)

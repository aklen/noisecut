"""
Parser for .NET/MSBuild compiler output

Handles:
- C# compiler warnings (CS####)
- System library warnings (SYSLIB####)
- Code analysis warnings (CA####)
- Roslyn analyzer warnings (IDE####)
- Third-party analyzer warnings (e.g., MsgPack####)
"""

import re
from typing import Optional, Tuple
from ..model import BuildIssue, BuildStats


class DotNetParser:
    """Parser for .NET MSBuild/Roslyn compiler output"""
    
    # Pattern: /path/to/file.cs(76,34): warning CS0168: The variable 'ex' is declared but never used
    ISSUE_PATTERN = re.compile(
        r'^\s*(.+?)\((\d+),(\d+)\):\s+(warning|error)\s+([A-Z][A-Z\d]+):\s+(.+?)(?:\s+\(https?://[^\)]+\))?$',
        re.IGNORECASE
    )
    
    # Pattern: Ape.Core net9.0 succeeded with 3 warning(s) (1.7s)
    BUILD_SUCCESS_PATTERN = re.compile(
        r'^\s*(.+?)\s+net\d+\.\d+\s+succeeded(?:\s+with\s+(\d+)\s+warning)?',
        re.IGNORECASE
    )
    
    # Pattern: Build succeeded with 6 warning(s) in 6.0s
    BUILD_SUMMARY_PATTERN = re.compile(
        r'^\s*Build\s+succeeded(?:\s+with\s+(\d+)\s+warning)?',
        re.IGNORECASE
    )
    
    # Pattern: Restore complete (1.2s)
    RESTORE_PATTERN = re.compile(
        r'^\s*Restore\s+complete',
        re.IGNORECASE
    )
    
    def __init__(self):
        self.stats = BuildStats()
        self.issues = []  # Store all parsed issues
        self.current_issue = None
    
    def parse_line(self, line: str) -> Optional[BuildIssue]:
        """
        Parse a single line of .NET build output.
        
        Args:
            line: Single line of build output
            
        Returns:
            BuildIssue if line contains warning/error, None otherwise
        """
        # Try to parse warning/error
        match = self.ISSUE_PATTERN.match(line)
        if match:
            file_path = match.group(1).strip()
            line_num = int(match.group(2))
            column = int(match.group(3))
            issue_type = match.group(4).lower()  # 'warning' or 'error'
            code = match.group(5)  # e.g., CS0168, SYSLIB0057
            message = match.group(6).strip()
            
            # Update stats
            if issue_type == 'warning':
                self.stats.warnings += 1
            elif issue_type == 'error':
                self.stats.errors += 1
            
            # Format category as -W style for consistency with other compilers
            category = f"-W{code}"
            
            issue = BuildIssue(
                type=issue_type,
                file=file_path,
                line=line_num,
                column=column,
                message=message,
                detail="",
                category=category
            )
            
            # Add to issues list
            self.issues.append(issue)
            
            return issue
        
        # Track build progress
        if self.BUILD_SUCCESS_PATTERN.match(line):
            self.stats.files_compiled += 1
        
        return None
    
    def get_stats(self) -> BuildStats:
        """Get build statistics"""
        return self.stats
    
    def finalize(self):
        """Finalize parsing (no-op for DotNet parser)"""
        pass
    
    @staticmethod
    def detect(lines: list) -> bool:
        """
        Detect if output is from .NET build.
        
        Args:
            lines: List of output lines
            
        Returns:
            True if output appears to be from .NET build
        """
        dotnet_indicators = 0
        
        for line in lines[:50]:  # Check first 50 lines
            # Look for .NET-specific patterns
            if 'net9.0' in line or 'net8.0' in line or 'net7.0' in line or 'net6.0' in line:
                dotnet_indicators += 1
            if 'Restore complete' in line:
                dotnet_indicators += 1
            if re.search(r'\([\d,]+\):\s+(warning|error)\s+[A-Z]{2}\d{4}:', line):
                dotnet_indicators += 2  # Strong indicator
            if 'succeeded with' in line and 'warning(s)' in line:
                dotnet_indicators += 1
            if line.strip().startswith('Build succeeded'):
                dotnet_indicators += 1
        
        return dotnet_indicators >= 2

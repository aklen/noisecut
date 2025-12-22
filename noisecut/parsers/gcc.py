"""
GCC/G++ compiler output parser
"""

import re
from typing import Optional
from pathlib import Path
from collections import deque

from .base import BaseParser
from ..model import BuildIssue
from ..utils import Color


class GccParser(BaseParser):
    """Parser for GCC and G++ compiler output (also handles Clang)"""
    
    def __init__(self):
        super().__init__()
        # Buffer last N lines to find linking target for linker warnings
        self._line_buffer = deque(maxlen=5)  # Keep last 5 lines
    
    # Patterns for compiler output
    COMPILE_PATTERN = re.compile(
        r'^\s*(?:.*?/)?(g\+\+|gcc|clang\+\+|clang|avr-gcc|avr-g\+\+).*?-o\s+(\S+)\s+(\S+)$'
    )
    
    # Pattern for make output with bullet points (e.g., "• Compiling src/main.c")
    MAKE_COMPILE_PATTERN = re.compile(
        r'^\s*[•▪◦-]\s+(?:Compiling|Building)\s+(.+)$'
    )
    
    MOC_PATTERN = re.compile(
        r'^\s*(?:.*?/)?moc\s+.*?-o\s+(\S+)\s+(\S+)$'
    )
    
    # Issue patterns
    ISSUE_PATTERN = re.compile(
        r'^(.*?):(\d+):(\d+):\s+(warning|error):\s+(.+?)(?:\s+\[([-\w=]+)\])?$'
    )
    
    # Linker error pattern (e.g., /path/file.c:211:(...): undefined reference to `symbol`)
    LINKER_ERROR_PATTERN = re.compile(
        r'^(.*?):(\d+):\([^)]+\):\s+(.+)$'
    )
    
    # Linker warning/error from ld (e.g., ld: warning: ignoring duplicate libraries: '-lc++')
    LD_WARNING_PATTERN = re.compile(
        r'^ld:\s+(warning|error):\s+(.+)$'
    )
    
    # CMake/Make linking line pattern (e.g., "[ 90%] Linking CXX shared library ../../lib/libFoo.dylib")
    LINKING_PATTERN = re.compile(
        r'^\s*\[\s*\d+%\]\s+Linking\s+(?:CXX|C)\s+(?:shared library|executable|static library)\s+(.+)$'
    )
    
    # Generic error pattern (e.g., collect2: error: ld returned 1 exit status)
    GENERIC_ERROR_PATTERN = re.compile(
        r'^collect2:\s+error:\s+(.+)$'
    )
    
    NOTE_PATTERN = re.compile(
        r'^(.*?):(\d+):(\d+):\s+note:\s+(.+)$'
    )
    
    DETAIL_PATTERN = re.compile(
        r'^\s+\d+\s+\|'  # Line showing source code context
    )
    
    def _extract_target_from_buffer(self) -> str:
        """Search line buffer backwards for most recent linking target."""
        # Search backwards through buffer for "Linking..." line
        for buffered_line in reversed(self._line_buffer):
            match = self.LINKING_PATTERN.match(buffered_line)
            if match:
                # Extract target name from path (e.g., "../../lib/libFoo.dylib" -> "libFoo.dylib")
                full_path = match.group(1)
                return Path(full_path).name
        return ""  # No target found
    
    def parse_line(self, line: str) -> Optional[str]:
        """Parse a single line of GCC output. Returns formatted line or None."""
        
        # Add to line buffer for linker target tracking
        self._line_buffer.append(line)
        
        # Check for compilation
        compile_match = self.COMPILE_PATTERN.match(line)
        if compile_match:
            self.stats.files_compiled += 1
            output_file = compile_match.group(2)
            source_file = compile_match.group(3)
            return self._format_compilation(source_file, output_file)
        
        # Check for make-style compilation output (• Compiling src/main.c)
        make_compile_match = self.MAKE_COMPILE_PATTERN.match(line)
        if make_compile_match:
            self.stats.files_compiled += 1
            source_file = make_compile_match.group(1)
            # Extract just the filename for display
            file_name = Path(source_file).name
            return f"{Color.CYAN}[CC]{Color.NC} {source_file}"
        
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
        
        # Check for linker errors (e.g., /path/file.c:211:(...): undefined reference)
        linker_match = self.LINKER_ERROR_PATTERN.match(line)
        if linker_match:
            file_path, line_num, message = linker_match.groups()
            
            # Save previous issue
            if self.current_issue:
                self.issues.append(self.current_issue)
            
            # Create new error issue
            self.current_issue = BuildIssue(
                type='error',
                file=file_path,
                line=int(line_num),
                column=0,
                message=message,
                category=""
            )
            
            self.stats.errors += 1
            return None
        
        # Check for linker warnings/errors from ld (e.g., ld: warning: ignoring duplicate libraries)
        ld_match = self.LD_WARNING_PATTERN.match(line)
        if ld_match:
            issue_type, message = ld_match.groups()
            
            # Save previous issue
            if self.current_issue:
                self.issues.append(self.current_issue)
            
            # Extract library/symbol names from quotes in the message
            import re
            quoted_items = re.findall(r"'([^']+)'", message)
            library_name = quoted_items[0] if quoted_items else ""
            
            # Try to find linking target from recent lines
            target_name = self._extract_target_from_buffer()
            
            # Create new issue with linker-specific type
            # Store: library_name|target_name in file field (pipe-separated)
            file_info = f"{library_name}|{target_name}" if target_name else library_name
            
            self.current_issue = BuildIssue(
                type=f'linker-{issue_type}',  # 'linker-warning' or 'linker-error'
                file=file_info,  # "library|target" or just "library"
                line=0,
                column=0,
                message=message,
                category=""
            )
            
            if issue_type == 'warning':
                self.stats.warnings += 1
            else:
                self.stats.errors += 1
            return None
        
        # Check for generic errors (e.g., collect2: error: ld returned 1 exit status)
        generic_error_match = self.GENERIC_ERROR_PATTERN.match(line)
        if generic_error_match:
            # Don't create a new issue, just note that build failed
            # The actual linker error was already captured above
            return None
        
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

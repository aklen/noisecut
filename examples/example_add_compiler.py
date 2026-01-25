"""
Example: Adding Rust Compiler Support

This demonstrates how easy it is to add a new compiler with the registry system.

Steps:
1. Create rust.py parser (implement BaseParser)
2. Register in builtin.py (3 lines!)
3. That's it! Auto-detection works automatically.
"""

# ============================================================
# STEP 1: Create parsers/rust.py
# ============================================================

from typing import Optional
import re
from ..model import BuildIssue, BuildStats
from .base import BaseParser


class RustParser(BaseParser):
    """Parser for Rust compiler (rustc) output"""
    
    # Rust format: error[E0308]: mismatched types
    ISSUE_PATTERN = re.compile(
        r'^(error|warning)(?:\[([A-Z]\d+)\])?: (.+)$'
    )
    
    # Location on separate line: --> src/main.rs:42:10
    LOCATION_PATTERN = re.compile(
        r'^\s*-->\s*(.+):(\d+):(\d+)$'
    )
    
    def __init__(self):
        super().__init__()
        self._pending_issue = None  # Store issue waiting for location
    
    def parse_line(self, line: str) -> Optional[BuildIssue]:
        # Try to match error/warning line
        match = self.ISSUE_PATTERN.match(line)
        if match:
            issue_type = match.group(1)
            code = match.group(2) or ""
            message = match.group(3)
            
            # Store for next line (location comes after)
            self._pending_issue = {
                'type': issue_type,
                'code': code,
                'message': message
            }
            return None
        
        # Try to match location line
        if self._pending_issue:
            loc_match = self.LOCATION_PATTERN.match(line)
            if loc_match:
                file_path = loc_match.group(1)
                line_num = int(loc_match.group(2))
                column = int(loc_match.group(3))
                
                # Create issue with stored data
                issue = BuildIssue(
                    type=self._pending_issue['type'],
                    file=file_path,
                    line=line_num,
                    column=column,
                    message=self._pending_issue['message'],
                    detail="",
                    category=f"-W{self._pending_issue['code']}"
                )
                
                self._pending_issue = None
                self.issues.append(issue)
                
                # Update stats
                if issue.type == 'warning':
                    self.stats.warnings += 1
                elif issue.type == 'error':
                    self.stats.errors += 1
                
                return issue
        
        return None


# ============================================================
# STEP 2: Register in builtin.py (ADD ONLY THESE 3 LINES!)
# ============================================================

# In noisecut/parsers/builtin.py, add:

from .rust import RustParser  # Import

register_compiler(
    key='rust',
    name='Rust Compiler',
    parser_class=RustParser,
    extensions=['.rs'],
    project_files=['Cargo.toml', 'Cargo.lock'],
    detection_keywords=['rustc', 'cargo', 'rust'],
    command_patterns=['rustc', 'cargo']
)

# DONE! That's literally it! ✨


# ============================================================
# STEP 3: Add severity mappings to severity.py (optional)
# ============================================================

# In noisecut/severity.py, add:

SEVERITY_MAP.update({
    # Rust critical errors
    "-WE0308": Severity.CRITICAL,  # Mismatched types
    "-WE0382": Severity.CRITICAL,  # Use of moved value
    "-WE0499": Severity.CRITICAL,  # Borrow of moved value
    
    # Rust warnings
    "-Wunused-variables": Severity.MEDIUM,
    "-Wdead-code": Severity.MEDIUM,
    "-Wdeprecated": Severity.LOW,
})


# ============================================================
# USAGE - Works immediately!
# ============================================================

"""
# Auto-detection works automatically:
cargo build 2>&1 | ncut

# Or explicit:
ncut --parser rust

# Help shows it:
ncut --help
# --parser {auto,gcc,clang,avr-gcc,dotnet,rust}
#                         ^^^^^ NEW!
"""


# ============================================================
# That's how easy it is! 🚀
# ============================================================

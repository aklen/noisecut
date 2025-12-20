#!/usr/bin/env python3
"""
noisecut
--------
Cut through compiler noise. See what really matters.
A build output analyzer for C/C++ projects that transforms raw compiler output
into clear, actionable insight.

Original author: Akos Hamori
Website: https://akoshamori.com/
"""

import subprocess
import sys
import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from pathlib import Path
import shutil

# ANSI color codes
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    NC = '\033[0m'  # No Color


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
    locations: List[Tuple[str, int, int]] = field(default_factory=list)
    
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


class BuildOutputParser:
    """Parses GCC/Clang compiler output"""
    
    # Patterns for compiler output
    COMPILE_PATTERN = re.compile(
        r'^\s*(?:.*?/)?clang\+\+.*?-o\s+(\S+)\s+(\S+)$'
    )
    
    MOC_PATTERN = re.compile(
        r'^\s*(?:.*?/)?moc\s+.*?-o\s+(\S+)\s+(\S+)$'
    )
    
    # Issue patterns
    ISSUE_PATTERN = re.compile(
        r'^(.*?):(\d+):(\d+):\s+(warning|error):\s+(.+?)(?:\s+\[([-\w]+)\])?$'
    )
    
    NOTE_PATTERN = re.compile(
        r'^(.*?):(\d+):(\d+):\s+note:\s+(.+)$'
    )
    
    DETAIL_PATTERN = re.compile(
        r'^\s+\d+\s+\|'  # Line showing source code context
    )
    
    def __init__(self):
        self.issues: List[BuildIssue] = []
        self.current_issue: Optional[BuildIssue] = None
        self.stats = BuildStats()
        
    def parse_line(self, line: str) -> Optional[str]:
        """Parse a single line of build output. Returns formatted line or None."""
        
        # Check for compilation
        compile_match = self.COMPILE_PATTERN.match(line)
        if compile_match:
            self.stats.files_compiled += 1
            output_file = Path(compile_match.group(1)).name
            source_file = Path(compile_match.group(2)).name
            return f"{Color.CYAN}[CC]{Color.NC} {source_file} → {output_file}"
        
        # Check for MOC
        moc_match = self.MOC_PATTERN.match(line)
        if moc_match:
            self.stats.moc_generated += 1
            output_file = Path(moc_match.group(1)).name
            source_file = Path(moc_match.group(2)).name
            return f"{Color.MAGENTA}[MOC]{Color.NC} {source_file} → {output_file}"
        
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
    
    def finalize(self):
        """Call when parsing is complete"""
        if self.current_issue:
            self.issues.append(self.current_issue)
            self.current_issue = None


def group_issues(issues: List[BuildIssue]) -> List[GroupedIssue]:
    """Group identical issues together"""
    groups: Dict[BuildIssue, GroupedIssue] = {}
    
    for issue in issues:
        # Create a key based on type, message, and category
        key_issue = BuildIssue(
            type=issue.type,
            file="",
            line=0,
            column=0,
            message=issue.message,
            category=issue.category,
            detail=issue.detail
        )
        
        if key_issue not in groups:
            groups[key_issue] = GroupedIssue(
                issue=key_issue,
                locations=[]
            )
        
        groups[key_issue].locations.append((issue.file, issue.line, issue.column))
    
    # Sort by count (most common first)
    return sorted(groups.values(), key=lambda g: g.count, reverse=True)


def format_issue_location(file_path: str, line: int, column: int) -> str:
    """Format a file location"""
    # Try to make path relative and shorter
    try:
        rel_path = Path(file_path).relative_to(Path.cwd())
        file_str = str(rel_path)
    except ValueError:
        # Extract just filename and parent directory
        path_obj = Path(file_path)
        if len(path_obj.parts) > 1:
            file_str = f"{path_obj.parts[-2]}/{path_obj.name}"
        else:
            file_str = path_obj.name
    
    return f"{file_str}:{line}:{column}"


def print_grouped_issues(grouped_issues: List[GroupedIssue], max_locations: int = 5):
    """Print grouped issues with colors"""
    if not grouped_issues:
        return
    
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    
    for group in grouped_issues:
        issue = group.issue
        
        # Color based on type
        if issue.type == 'error':
            color = Color.RED
            icon = "✗"
        else:
            color = Color.YELLOW
            icon = "⚠"
        
        # Header
        print(f"\n{color}{Color.BOLD}{icon} {issue.type.upper()}{Color.NC}: {issue.message}")
        
        if issue.category:
            print(f"  {Color.DIM}Category: {issue.category}{Color.NC}")
        
        if issue.detail:
            print(f"  {Color.DIM}{issue.detail}{Color.NC}")
        
        # Locations
        print(f"  {Color.BOLD}Occurrences ({group.count}):{Color.NC}")
        
        for i, (file_path, line, col) in enumerate(group.locations[:max_locations]):
            location = format_issue_location(file_path, line, col)
            
            # Wrap long paths
            if len(location) > terminal_width - 6:
                location = "..." + location[-(terminal_width - 9):]
            
            print(f"    {Color.CYAN}{location}{Color.NC}")
        
        if group.count > max_locations:
            remaining = group.count - max_locations
            print(f"    {Color.DIM}... and {remaining} more{Color.NC}")


def print_stats(stats: BuildStats, success: bool):
    """Print build statistics"""
    print(f"\n{Color.BOLD}{'─' * 60}{Color.NC}")
    print(f"{Color.BOLD}Build Statistics{Color.NC}")
    print(f"{Color.BOLD}{'─' * 60}{Color.NC}")
    
    if success:
        status_color = Color.GREEN
        status_icon = "✓"
        status_text = "SUCCESS"
    else:
        status_color = Color.RED
        status_icon = "✗"
        status_text = "FAILED"
    
    print(f"{status_color}{Color.BOLD}{status_icon} Build {status_text}{Color.NC}")
    print(f"  Files compiled: {Color.CYAN}{stats.files_compiled}{Color.NC}")
    print(f"  MOC generated:  {Color.MAGENTA}{stats.moc_generated}{Color.NC}")
    print(f"  Warnings:       {Color.YELLOW}{stats.warnings}{Color.NC}")
    print(f"  Errors:         {Color.RED}{stats.errors}{Color.NC}")
    
    if stats.duration > 0:
        print(f"  Duration:       {Color.CYAN}{stats.duration:.2f}s{Color.NC}")
    
    print(f"{Color.BOLD}{'─' * 60}{Color.NC}")


def run_build(command: List[str], verbose: bool = False) -> Tuple[int, BuildStats, List[BuildIssue]]:
    """Run build command and parse output"""
    import time
    
    parser = BuildOutputParser()
    start_time = time.time()
    
    print(f"{Color.BOLD}Running:{Color.NC} {' '.join(command)}\n")
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            line = line.rstrip()
            
            # Parse line
            formatted = parser.parse_line(line)
            
            # Print if verbose or it's a formatted message
            if verbose:
                print(line)
            elif formatted:
                print(formatted)
        
        return_code = process.wait()
        
    except FileNotFoundError:
        print(f"{Color.RED}Error: Command not found: {command[0]}{Color.NC}")
        return 1, parser.stats, []
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}Build interrupted{Color.NC}")
        process.kill()
        return 130, parser.stats, []
    
    parser.finalize()
    parser.stats.duration = time.time() - start_time
    
    return return_code, parser.stats, parser.issues


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build wrapper for gnss_controller with enhanced error reporting'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show all compiler output (not just summary)'
    )
    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=8,
        help='Number of parallel jobs (default: 8)'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean before building'
    )
    parser.add_argument(
        '--max-locations',
        type=int,
        default=5,
        help='Maximum locations to show per issue (default: 5)'
    )
    parser.add_argument(
        'target',
        nargs='?',
        default=None,
        help='Make target (default: all)'
    )
    
    args = parser.parse_args()
    
    # Change to build directory if not already there
    if not os.path.exists('Makefile'):
        if os.path.exists('build/Makefile'):
            os.chdir('build')
            print(f"{Color.CYAN}Changed to build directory{Color.NC}\n")
        else:
            print(f"{Color.RED}Error: No Makefile found. Run qmake first.{Color.NC}")
            return 1
    
    # Clean if requested
    if args.clean:
        print(f"{Color.YELLOW}Cleaning...{Color.NC}")
        subprocess.run(['make', 'clean'], capture_output=True)
        print()
    
    # Build command
    command = ['make', f'-j{args.jobs}']
    if args.target:
        command.append(args.target)
    
    # Run build
    return_code, stats, issues = run_build(command, args.verbose)
    
    # Print issues if any
    if issues:
        print(f"\n{Color.BOLD}{'=' * 60}{Color.NC}")
        print(f"{Color.BOLD}Issue Summary{Color.NC}")
        print(f"{Color.BOLD}{'=' * 60}{Color.NC}")
        
        grouped = group_issues(issues)
        print_grouped_issues(grouped, args.max_locations)
    
    # Print statistics
    print_stats(stats, return_code == 0)
    
    # Exit with build return code
    return return_code


if __name__ == '__main__':
    sys.exit(main())

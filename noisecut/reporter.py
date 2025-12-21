"""
Output formatting and reporting
"""

from typing import List
from pathlib import Path

from .model import GroupedIssue, BuildStats
from .utils import Color, get_terminal_width
from .severity import get_severity, get_severity_color, Severity


def format_issue_location(file_path: str, line: int, column: int) -> str:
    """
    Format a file location in a readable way.
    
    Tries to make the path relative and shorter for better readability.
    
    Args:
        file_path: Full file path
        line: Line number
        column: Column number
        
    Returns:
        Formatted location string like "src/file.cpp:123:45"
    """
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


def print_issue_summary(grouped_issues: List[GroupedIssue], max_locations: int = 5, 
                        show_severity: bool = True):
    """
    Print grouped issues with colors and formatting.
    Issues are sorted by severity (least important first, most important last)
    so that critical issues appear at the bottom of the terminal output.
    
    Args:
        grouped_issues: List of grouped issues to display
        max_locations: Maximum number of locations to show per issue
        show_severity: Whether to show severity levels for warnings
    """
    if not grouped_issues:
        return
    
    terminal_width = get_terminal_width()
    
    # Sort by severity: LOW/INFO first, CRITICAL/HIGH last
    # This puts the most important issues at the bottom of the output
    severity_order = {
        Severity.INFO: 0,
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4,
        None: 5  # Unknown severity (shouldn't happen, but just in case)
    }
    
    def get_sort_key(group: GroupedIssue):
        issue = group.issue
        # Errors always last (most important)
        if issue.type == 'error':
            return (99, 0, -group.count)  # Errors at the very end
        # Warnings sorted by severity
        severity = get_severity(issue.category) if issue.category else None
        return (
            severity_order.get(severity, 5),  # Severity level
            -group.count  # More occurrences first within same severity
        )
    
    sorted_issues = sorted(grouped_issues, key=get_sort_key)
    
    for group in sorted_issues:
        issue = group.issue
        
        # Determine severity for warnings
        severity = None
        if issue.type == 'warning' and issue.category and show_severity:
            severity = get_severity(issue.category)
        
        # Color and formatting
        if issue.type == 'error':
            color = Color.RED
            icon = "✗"
            header_suffix = ""
        else:
            # Warnings are always YELLOW
            color = Color.YELLOW
            icon = "⚠"
            
            # But HIGH/CRITICAL badges are RED
            if severity and severity in [Severity.CRITICAL, Severity.HIGH]:
                header_suffix = f"{Color.NC} [{Color.RED}{Color.BOLD}{severity}{Color.NC}]"
            elif severity in [Severity.LOW, Severity.INFO]:
                header_suffix = f"{Color.NC} [{Color.CYAN}{severity}{Color.NC}]"
            else:
                header_suffix = ""
        
        # Header: WARNING always yellow, but severity badge can be red
        print(f"\n{color}{Color.BOLD}{icon} {issue.type.upper()}{Color.NC}{header_suffix}: {issue.message}")
        
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


def print_build_stats(stats: BuildStats, success: bool):
    """
    Print build statistics summary.
    
    Args:
        stats: BuildStats object with compilation statistics
        success: Whether the build succeeded
    """
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

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
        if issue.type == 'error' or issue.type == 'linker-error':
            return (99, 0, -group.count)  # Errors at the very end
        # Linker warnings: medium priority (after regular warnings)
        if issue.type == 'linker-warning':
            return (50, -group.count)
        # Regular warnings sorted by severity
        severity = get_severity(issue.category) if issue.category else None
        return (
            severity_order.get(severity, 5),  # Severity level
            -group.count  # More occurrences first within same severity
        )
    
    sorted_issues = sorted(grouped_issues, key=get_sort_key)
    
    for group in sorted_issues:
        issue = group.issue
        
        # Check if this is a linker issue
        is_linker = issue.type.startswith('linker-')
        
        # Determine severity for warnings
        severity = None
        if issue.type == 'warning' and issue.category and show_severity:
            severity = get_severity(issue.category)
        
        # Color and formatting
        if issue.type == 'error' or issue.type == 'linker-error':
            color = Color.RED
            icon = "✗"
            header_suffix = ""
            type_label = "LINKER ERROR" if is_linker else "ERROR"
        else:
            # Warnings are always YELLOW
            color = Color.YELLOW
            icon = "⚠"
            type_label = "LINKER WARNING" if is_linker else "WARNING"
            
            # But HIGH/CRITICAL badges are RED, MEDIUM is white, LOW/INFO is cyan
            if severity and severity in [Severity.CRITICAL, Severity.HIGH]:
                header_suffix = f"{Color.NC} [{Color.RED}{Color.BOLD}{severity}{Color.NC}]"
            elif severity == Severity.MEDIUM:
                header_suffix = f"{Color.NC} [{severity}]"  # White (default terminal color)
            elif severity in [Severity.LOW, Severity.INFO]:
                header_suffix = f"{Color.NC} [{Color.CYAN}{severity}{Color.NC}]"
            else:
                header_suffix = ""
        
        # Format message for better readability
        display_message = issue.message
        
        # Improve deprecated warnings: "is deprecated: Use X" -> "found deprecated ...: use X"
        if issue.category == "-Wdeprecated-declarations":
            import re
            # Pattern: "is deprecated: Use X instead"
            match = re.match(r"^is deprecated:\s*(.+)$", display_message, re.IGNORECASE)
            if match:
                suggestion = match.group(1)
                # Lowercase "Use" to "use" for consistency
                suggestion = suggestion[0].lower() + suggestion[1:] if suggestion else suggestion
                display_message = f"found deprecated declaration: {suggestion}"
        
        # Header: WARNING always yellow, but severity badge can be red
        print(f"\n{color}{Color.BOLD}{icon} {type_label}{Color.NC}{header_suffix}: {display_message}")
        
        if issue.category:
            print(f"  {Color.DIM}Category: {issue.category}{Color.NC}")
        
        if issue.detail:
            print(f"  {Color.DIM}{issue.detail}{Color.NC}")
        
        # Locations (skip for linker issues since they have no source location)
        if not is_linker:
            print(f"  {Color.BOLD}Occurrences ({group.count}):{Color.NC}")
            
            for i, location_data in enumerate(group.locations[:max_locations]):
                # Handle both old (3-tuple) and new (4-tuple) format
                if len(location_data) == 4:
                    file_path, line, col, original_msg = location_data
                else:
                    file_path, line, col = location_data
                    original_msg = None
                
                location = format_issue_location(file_path, line, col)
                
                # Wrap long paths
                if len(location) > terminal_width - 6:
                    location = "..." + location[-(terminal_width - 9):]
            
                # Extract variable/function name from original message if different from grouped message
                detail_suffix = ""
                if original_msg and original_msg != group.issue.message:
                    # Extract quoted parts (variable names, etc.)
                    import re
                    quoted = re.findall(r"'([^']*)'", original_msg)
                    if quoted:
                        detail_suffix = f" {Color.DIM}({', '.join(quoted)}){Color.NC}"
                
                print(f"    {Color.CYAN}{location}{Color.NC}{detail_suffix}")
            
            if group.count > max_locations:
                remaining = group.count - max_locations
                print(f"    {Color.DIM}... and {remaining} more{Color.NC}")
        else:
            # For linker issues, show affected libraries/symbols and targets
            print(f"  {Color.BOLD}Occurrences: {group.count}{Color.NC}")
            
            # Parse file field: can be "library" or "library|target"
            lib_target_pairs = []
            for loc in group.locations:
                file_info = loc[0]  # Can be "library|target" or just "library"
                if '|' in file_info:
                    lib, target = file_info.split('|', 1)
                    lib_target_pairs.append((lib, target))
                elif file_info:
                    lib_target_pairs.append((file_info, None))
            
            # Group by library
            libs_with_targets = {}
            for lib, target in lib_target_pairs:
                if lib not in libs_with_targets:
                    libs_with_targets[lib] = set()
                if target:
                    libs_with_targets[lib].add(target)
            
            # Display libraries and their affected targets
            for lib in sorted(libs_with_targets.keys()):
                targets = libs_with_targets[lib]
                if targets:
                    print(f"    {Color.CYAN}{lib}{Color.NC} (in: {Color.DIM}{', '.join(sorted(targets))}{Color.NC})")
                else:
                    print(f"    {Color.CYAN}{lib}{Color.NC}")


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

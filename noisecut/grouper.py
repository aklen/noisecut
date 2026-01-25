"""
Issue grouping logic
"""

from typing import List, Dict
import re
from .model import BuildIssue, GroupedIssue


def normalize_path_for_dedup(file_path: str) -> str:
    """
    Normalize file path for deduplication using last 3 path components.
    
    This handles different relative paths while distinguishing files 
    with same names in different directories.
    
    Examples:
        ../../src/window/EMainTab/emaintab.h -> window/EMainTab/emaintab.h
        ../drivers/gps/sensor.cpp -> drivers/gps/sensor.cpp
        src/utils/logger.cpp -> utils/logger.cpp (distinct from drivers/logger.cpp)
    
    Args:
        file_path: Original file path (may be relative with .. or ./)
        
    Returns:
        Normalized path using last 3 components
    """
    parts = file_path.replace('\\', '/').split('/')
    # Filter out .., ., moc, build, obj directories
    clean_parts = [p for p in parts if p and p not in ('..', '.', 'moc', 'build', 'obj', 'out')]
    
    # Take last 3 components (dir/subdir/file.h)
    # Falls back to full path if less than 3 components
    return '/'.join(clean_parts[-3:]) if len(clean_parts) >= 3 else '/'.join(clean_parts)


def normalize_message(message: str, category: str) -> str:
    """
    Normalize warning/error message for grouping.
    
    For warnings with specific variable/function names, strip them out
    so similar warnings group together (e.g., "unused parameter 'x'" 
    and "unused parameter 'y'" become "unused parameter").
    
    Args:
        message: Original warning/error message
        category: Warning category (e.g., -Wunused-parameter)
        
    Returns:
        Normalized message for grouping
    """
    # Remove quoted strings (variable names, function names, etc.)
    # e.g., "unused parameter 'flags'" -> "unused parameter"
    normalized = re.sub(r"'[^']*'", "", message)
    normalized = re.sub(r'"[^"]*"', "", normalized)
    normalized = re.sub(r"'[^']*'", "", normalized)  # Unicode quotes
    
    # For sign-compare warnings, strip type names to group similar warnings
    # e.g., "comparison of integers of different signs: 'int' and 'unsigned long'" 
    # -> "comparison of integers of different signs: and"
    if "comparison" in normalized.lower() or category == "-Wsign-compare":
        # Remove everything after "signs:" to strip all type information
        # Handles both "signs: int and unsigned long" and "signs: int and size_type (aka unsigned long)"
        normalized = re.sub(r"signs:.*$", "signs: and", normalized)
    
    # Clean up extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Remove trailing punctuation and "did you mean X?" suggestions
    normalized = re.sub(r';\s*did you mean.*$', '', normalized)
    normalized = re.sub(r'\?.*$', '', normalized)
    
    return normalized


def group_issues(issues: List[BuildIssue]) -> List[GroupedIssue]:
    """
    Group similar issues together.
    
    Issues are grouped by type, normalized message, and category.
    This allows grouping "unused parameter 'x'" and "unused parameter 'y'" together.
    
    Args:
        issues: List of BuildIssue objects
        
    Returns:
        List of GroupedIssue objects, sorted by occurrence count (descending)
    """
    groups: Dict[tuple, GroupedIssue] = {}
    
    for issue in issues:
        # Normalize message for grouping
        normalized_msg = normalize_message(issue.message, issue.category)
        
        # Create a grouping key
        key = (issue.type, normalized_msg, issue.category)
        
        if key not in groups:
            # Create new group with normalized message
            key_issue = BuildIssue(
                type=issue.type,
                file="",
                line=0,
                column=0,
                message=normalized_msg,
                category=issue.category,
                detail=issue.detail
            )
            groups[key] = GroupedIssue(
                issue=key_issue,
                locations=[]
            )
        
        # Add location with original message (for showing variable names)
        location = (issue.file, issue.line, issue.column, issue.message)
        
        # For linker issues, don't deduplicate - just count occurrences
        is_linker = issue.type.startswith('linker-')
        if is_linker:
            # Always add linker issues to track occurrence count
            groups[key].locations.append(location)
        else:
            # Deduplicate based on normalized path + line + column
            # This handles different relative paths to the same file
            normalized_path = normalize_path_for_dedup(issue.file)
            location_key = (normalized_path, issue.line, issue.column)
            existing_locations = [(normalize_path_for_dedup(f), l, c) for f, l, c, _ in groups[key].locations]
            if location_key not in existing_locations:
                groups[key].locations.append(location)
    
    # Sort by count (most common first)
    return sorted(groups.values(), key=lambda g: g.count, reverse=True)

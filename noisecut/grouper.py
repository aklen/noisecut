"""
Issue grouping logic
"""

from typing import List, Dict
from .model import BuildIssue, GroupedIssue


def group_issues(issues: List[BuildIssue]) -> List[GroupedIssue]:
    """
    Group identical issues together.
    
    Issues are considered identical if they have the same type, message, and category,
    regardless of file location.
    
    Args:
        issues: List of BuildIssue objects
        
    Returns:
        List of GroupedIssue objects, sorted by occurrence count (descending)
    """
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

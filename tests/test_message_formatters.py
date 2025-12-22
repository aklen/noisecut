"""
Tests for message formatting functionality
"""

import pytest
from noisecut.model import BuildIssue
from noisecut.reporter import print_issue_summary
from noisecut.grouper import GroupedIssue
from io import StringIO
import sys


class TestDeprecatedMessageFormatting:
    """Test deprecated warning message formatting"""
    
    def capture_output(self, grouped_issues, max_locations=5, show_severity=True):
        """Helper to capture print_issue_summary output"""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        try:
            print_issue_summary(grouped_issues, max_locations, show_severity)
            return captured_output.getvalue()
        finally:
            sys.stdout = old_stdout
    
    def test_deprecated_use_format(self):
        """Test 'is deprecated: Use X' is formatted correctly"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use checkStateChanged() instead",
            category="-Wdeprecated-declarations",
            detail="'stateChanged' has been explicitly marked deprecated here"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "is deprecated: Use checkStateChanged() instead")]
        )
        
        output = self.capture_output([grouped])
        
        assert "found deprecated declaration: use checkStateChanged() instead" in output
        assert "is deprecated: Use" not in output  # Old format should not appear
    
    def test_deprecated_lowercase_use(self):
        """Test that 'Use' is lowercased to 'use'"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use std::as_const() instead",
            category="-Wdeprecated-declarations"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "is deprecated: Use std::as_const() instead")]
        )
        
        output = self.capture_output([grouped])
        
        assert "use std::as_const()" in output
        assert "Use std::as_const()" not in output  # Capital U should not appear
    
    def test_deprecated_with_period(self):
        """Test deprecated message with trailing period"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use std::as_const() instead.",
            category="-Wdeprecated-declarations"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "is deprecated: Use std::as_const() instead.")]
        )
        
        output = self.capture_output([grouped])
        
        assert "use std::as_const() instead." in output
    
    def test_deprecated_category_required(self):
        """Test that formatting only applies with correct category"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use something() instead",
            category="-Wother-warning"  # Different category
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "is deprecated: Use something() instead")]
        )
        
        output = self.capture_output([grouped])
        
        # Should NOT be formatted since category doesn't match
        assert "is deprecated: Use something() instead" in output
        assert "found deprecated declaration" not in output
    
    def test_deprecated_multiple_occurrences(self):
        """Test formatting with multiple occurrences"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use newFunc() instead",
            category="-Wdeprecated-declarations"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[
                ("test1.cpp", 42, 10, "is deprecated: Use newFunc() instead"),
                ("test2.cpp", 50, 15, "is deprecated: Use newFunc() instead"),
                ("test3.cpp", 88, 20, "is deprecated: Use newFunc() instead")
            ]
        )
        
        output = self.capture_output([grouped])
        
        assert "found deprecated declaration: use newFunc() instead" in output
        assert "Occurrences (3)" in output
    
    def test_deprecated_with_detail(self):
        """Test that detail message is preserved"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use checkStateChanged() instead",
            category="-Wdeprecated-declarations",
            detail="'stateChanged' has been explicitly marked deprecated here"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "is deprecated: Use checkStateChanged() instead")]
        )
        
        output = self.capture_output([grouped])
        
        assert "found deprecated declaration: use checkStateChanged() instead" in output
        assert "'stateChanged' has been explicitly marked deprecated here" in output
    
    def test_deprecated_case_insensitive_match(self):
        """Test that pattern matching is case insensitive"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="IS DEPRECATED: Use newFunc() instead",  # All caps
            category="-Wdeprecated-declarations"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "IS DEPRECATED: Use newFunc() instead")]
        )
        
        output = self.capture_output([grouped])
        
        assert "found deprecated declaration: use newFunc() instead" in output
    
    def test_non_deprecated_warning_unchanged(self):
        """Test that non-deprecated warnings are not affected"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="unused parameter 'foo'",
            category="-Wunused-parameter"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "unused parameter 'foo'")]
        )
        
        output = self.capture_output([grouped])
        
        assert "unused parameter" in output
        assert "found deprecated declaration" not in output
    
    def test_deprecated_severity_badge_shown(self):
        """Test that MEDIUM severity badge is shown for deprecated warnings"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use newFunc() instead",
            category="-Wdeprecated-declarations"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "is deprecated: Use newFunc() instead")]
        )
        
        output = self.capture_output([grouped], show_severity=True)
        
        assert "[MEDIUM]" in output
    
    def test_deprecated_formatting_preserves_category(self):
        """Test that warning category is still displayed"""
        issue = BuildIssue(
            type="warning",
            file="test.cpp",
            line=42,
            column=10,
            message="is deprecated: Use newFunc() instead",
            category="-Wdeprecated-declarations"
        )
        
        grouped = GroupedIssue(
            issue=issue,
            locations=[("test.cpp", 42, 10, "is deprecated: Use newFunc() instead")]
        )
        
        output = self.capture_output([grouped])
        
        assert "Category: -Wdeprecated-declarations" in output

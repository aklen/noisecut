#!/usr/bin/env python3
"""
Tests for grouping logic
"""

import pytest
from noisecut.grouper import normalize_path_for_dedup, normalize_message, group_issues
from noisecut.model import BuildIssue, GroupedIssue


class TestNormalizeMessage:
    """Tests for normalize_message function"""
    
    def test_remove_single_quoted_strings(self):
        """Should remove single-quoted variable names"""
        msg = "unused parameter 'flags'"
        result = normalize_message(msg, "-Wunused-parameter")
        assert result == "unused parameter"
    
    def test_remove_double_quoted_strings(self):
        """Should remove double-quoted strings"""
        msg = 'comparison between "int" and "unsigned"'
        result = normalize_message(msg, "-Wsign-compare")
        assert "int" not in result
        assert "unsigned" not in result
    
    def test_remove_unicode_quotes(self):
        """Should remove unicode-quoted strings"""
        msg = "unused variable 'counter'"
        result = normalize_message(msg, "-Wunused-variable")
        assert result == "unused variable"
    
    def test_sign_compare_type_stripping(self):
        """Should strip type information from sign-compare warnings"""
        msg = "comparison of integers of different signs: 'int' and 'unsigned long'"
        result = normalize_message(msg, "-Wsign-compare")
        # The normalization should strip everything after "signs:"
        assert result == "comparison of integers of different signs: and"
        # Verify quoted types are removed (note: 'integers' contains 'int' so we can't check that)
        assert "'int'" not in result
        assert "unsigned long" not in result
    
    def test_sign_compare_with_aka(self):
        """Should handle sign-compare with 'aka' type aliases"""
        msg = "comparison of integers of different signs: 'int' and 'size_type' (aka 'unsigned long')"
        result = normalize_message(msg, "-Wsign-compare")
        assert result == "comparison of integers of different signs: and"
        assert "size_type" not in result
        assert "aka" not in result
    
    def test_sign_compare_by_category(self):
        """Should strip types when category is -Wsign-compare"""
        msg = "comparison between signed and unsigned integer expressions"
        result = normalize_message(msg, "-Wsign-compare")
        # Should trigger the sign-compare normalization
        assert "and" in result
    
    def test_remove_did_you_mean_suggestions(self):
        """Should remove 'did you mean X?' suggestions"""
        msg = "unknown option 'foo'; did you mean 'bar'?"
        result = normalize_message(msg, "-Wunknown-option")
        assert "did you mean" not in result
        # The result has trailing space after semicolon removal - that's fine
        assert result.strip() == "unknown option"
    
    def test_remove_question_mark_suggestions(self):
        """Should remove trailing question mark suggestions"""
        msg = "implicit conversion loses precision; use explicit cast?"
        result = normalize_message(msg, "-Wconversion")
        assert "?" not in result
        assert result == "implicit conversion loses precision; use explicit cast"
    
    def test_clean_extra_whitespace(self):
        """Should collapse multiple spaces into one"""
        msg = "unused    parameter   'x'"
        result = normalize_message(msg, "-Wunused-parameter")
        assert "  " not in result
        assert result == "unused parameter"
    
    def test_preserve_basic_message(self):
        """Should preserve basic messages without quoted strings"""
        msg = "implicit declaration of function"
        result = normalize_message(msg, "-Wimplicit-function-declaration")
        assert result == msg
    
    def test_multiple_quoted_strings(self):
        """Should remove all quoted strings in a message"""
        msg = "conversion from 'int' to 'float' may alter its value"
        result = normalize_message(msg, "-Wconversion")
        assert result == "conversion from to may alter its value"
    
    def test_empty_quotes(self):
        """Should handle empty quotes"""
        msg = "unused parameter ''"
        result = normalize_message(msg, "-Wunused-parameter")
        assert result == "unused parameter"
    
    def test_nested_quotes(self):
        """Should handle nested quotes"""
        msg = "type 'std::vector<int>' does not match"
        result = normalize_message(msg, "-Wtype-mismatch")
        assert "std::vector" not in result


class TestGroupIssues:
    """Tests for group_issues function"""
    
    def test_group_identical_messages(self):
        """Should group issues with identical messages"""
        issues = [
            BuildIssue("warning", "test.cpp", 10, 5, "unused variable 'x'", "", "-Wunused-variable"),
            BuildIssue("warning", "test.cpp", 20, 5, "unused variable 'y'", "", "-Wunused-variable"),
            BuildIssue("warning", "test.cpp", 30, 5, "unused variable 'z'", "", "-Wunused-variable"),
        ]
        
        groups = group_issues(issues)
        assert len(groups) == 1
        assert groups[0].count == 3
        assert groups[0].issue.category == "-Wunused-variable"
    
    def test_separate_different_categories(self):
        """Should not group issues with different categories"""
        issues = [
            BuildIssue("warning", "test.cpp", 10, 5, "unused variable 'x'", "", "-Wunused-variable"),
            BuildIssue("warning", "test.cpp", 20, 5, "unused parameter 'y'", "", "-Wunused-parameter"),
        ]
        
        groups = group_issues(issues)
        assert len(groups) == 2
    
    def test_separate_different_types(self):
        """Should not group warnings and errors together"""
        issues = [
            BuildIssue("warning", "test.cpp", 10, 5, "unused variable 'x'", "", "-Wunused-variable"),
            BuildIssue("error", "test.cpp", 20, 5, "unused variable 'y'", "", "-Wunused-variable"),
        ]
        
        groups = group_issues(issues)
        assert len(groups) == 2
    
    def test_sort_by_count_descending(self):
        """Should sort groups by occurrence count (descending)"""
        issues = [
            # 3 occurrences of unused variable
            BuildIssue("warning", "test.cpp", 10, 5, "unused variable 'x'", "", "-Wunused-variable"),
            BuildIssue("warning", "test.cpp", 20, 5, "unused variable 'y'", "", "-Wunused-variable"),
            BuildIssue("warning", "test.cpp", 30, 5, "unused variable 'z'", "", "-Wunused-variable"),
            # 1 occurrence of unused parameter
            BuildIssue("warning", "test.cpp", 40, 5, "unused parameter 'p'", "", "-Wunused-parameter"),
        ]
        
        groups = group_issues(issues)
        assert len(groups) == 2
        assert groups[0].count == 3
        assert groups[1].count == 1
    
    def test_track_all_locations(self):
        """Should track all locations for grouped issues"""
        issues = [
            BuildIssue("warning", "test1.cpp", 10, 5, "unused variable 'x'", "", "-Wunused-variable"),
            BuildIssue("warning", "test2.cpp", 20, 5, "unused variable 'y'", "", "-Wunused-variable"),
        ]
        
        groups = group_issues(issues)
        assert len(groups) == 1
        assert len(groups[0].locations) == 2
        assert groups[0].locations[0][0] == "test1.cpp"  # file
        assert groups[0].locations[1][0] == "test2.cpp"  # file
    
    def test_empty_list(self):
        """Should handle empty issue list"""
        groups = group_issues([])
        assert len(groups) == 0
    
    def test_single_issue(self):
        """Should handle single issue"""
        issues = [
            BuildIssue("warning", "test.cpp", 10, 5, "unused variable 'x'", "", "-Wunused-variable"),
        ]
        
        groups = group_issues(issues)
        assert len(groups) == 1
        assert groups[0].count == 1

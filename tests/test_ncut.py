"""
Unit tests for noisecut build output analyzer
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import ncut
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from ncut import (
    BuildOutputParser,
    BuildIssue,
    group_issues,
    parse_from_file
)


class TestBuildOutputParser:
    """Test the BuildOutputParser class"""
    
    def test_parse_gcc_compilation(self):
        """Test parsing GCC compilation line"""
        parser = BuildOutputParser()
        line = "g++ -c -pipe -O2 -Wall -o main.o ../src/main.cpp"
        result = parser.parse_line(line)
        
        assert result is not None
        assert "main.cpp" in result
        assert "main.o" in result
        assert parser.stats.files_compiled == 1
    
    def test_parse_clang_compilation(self):
        """Test parsing Clang compilation line"""
        parser = BuildOutputParser()
        line = "clang++ -c -std=c++14 -stdlib=libc++ -o window.o ../src/window.cpp"
        result = parser.parse_line(line)
        
        assert result is not None
        assert "window.cpp" in result
        assert parser.stats.files_compiled == 1
    
    def test_parse_moc_generation(self):
        """Test parsing Qt MOC line"""
        parser = BuildOutputParser()
        line = "/opt/homebrew/share/qt/libexec/moc -DQT_NO_DEBUG -o moc_window.cpp ../src/window.h"
        result = parser.parse_line(line)
        
        assert result is not None
        assert "window.h" in result
        assert parser.stats.moc_generated == 1
    
    def test_parse_warning(self):
        """Test parsing a warning"""
        parser = BuildOutputParser()
        line = "../src/utils.cpp:45:23: warning: unused parameter 'flags' [-Wunused-parameter]"
        result = parser.parse_line(line)
        
        parser.finalize()
        
        assert parser.stats.warnings == 1
        assert len(parser.issues) == 1
        
        issue = parser.issues[0]
        assert issue.type == "warning"
        assert "utils.cpp" in issue.file
        assert issue.line == 45
        assert issue.column == 23
        assert "unused parameter" in issue.message
        assert issue.category == "-Wunused-parameter"
    
    def test_parse_error(self):
        """Test parsing an error"""
        parser = BuildOutputParser()
        line = "../src/manager.cpp:67:23: error: no matching function for call to 'clamp'"
        result = parser.parse_line(line)
        
        parser.finalize()
        
        assert parser.stats.errors == 1
        assert len(parser.issues) == 1
        
        issue = parser.issues[0]
        assert issue.type == "error"
        assert "manager.cpp" in issue.file
        assert issue.line == 67
        assert "no matching function" in issue.message
    
    def test_parse_note_context(self):
        """Test parsing note (additional context)"""
        parser = BuildOutputParser()
        
        # First parse the warning
        warning_line = "../src/controller.cpp:78:10: warning: 'initialize' overrides a member function but is not marked 'override' [-Winconsistent-missing-override]"
        parser.parse_line(warning_line)
        
        # Then parse the note
        note_line = "../include/base.h:23:18: note: overridden virtual function is here"
        parser.parse_line(note_line)
        
        parser.finalize()
        
        assert len(parser.issues) == 1
        issue = parser.issues[0]
        assert issue.detail == "overridden virtual function is here"
    
    def test_multiple_warnings(self):
        """Test parsing multiple warnings"""
        parser = BuildOutputParser()
        
        lines = [
            "../src/utils.cpp:45:23: warning: unused parameter 'flags' [-Wunused-parameter]",
            "../src/utils.cpp:89:10: warning: unused parameter 'options' [-Wunused-parameter]",
            "../src/main.cpp:123:5: warning: unused variable 'result' [-Wunused-variable]"
        ]
        
        for line in lines:
            parser.parse_line(line)
        
        parser.finalize()
        
        assert parser.stats.warnings == 3
        assert len(parser.issues) == 3


class TestIssueGrouping:
    """Test issue grouping functionality"""
    
    def test_group_identical_warnings(self):
        """Test grouping identical warnings from different files"""
        issues = [
            BuildIssue(
                type="warning",
                file="file1.cpp",
                line=10,
                column=5,
                message="unused parameter 'flags'",
                category="-Wunused-parameter"
            ),
            BuildIssue(
                type="warning",
                file="file2.cpp",
                line=20,
                column=10,
                message="unused parameter 'flags'",
                category="-Wunused-parameter"
            ),
            BuildIssue(
                type="warning",
                file="file3.cpp",
                line=30,
                column=15,
                message="unused variable 'result'",
                category="-Wunused-variable"
            )
        ]
        
        grouped = group_issues(issues)
        
        # Should have 2 groups (one for unused parameter, one for unused variable)
        assert len(grouped) == 2
        
        # First group should have 2 occurrences (sorted by count)
        assert grouped[0].count == 2
        assert grouped[1].count == 1
    
    def test_group_preserves_locations(self):
        """Test that grouping preserves all file locations"""
        issues = [
            BuildIssue(
                type="warning",
                file="a.cpp",
                line=10,
                column=5,
                message="test warning",
                category="-Wtest"
            ),
            BuildIssue(
                type="warning",
                file="b.cpp",
                line=20,
                column=10,
                message="test warning",
                category="-Wtest"
            )
        ]
        
        grouped = group_issues(issues)
        
        assert len(grouped) == 1
        assert len(grouped[0].locations) == 2
        assert ("a.cpp", 10, 5) in grouped[0].locations
        assert ("b.cpp", 20, 10) in grouped[0].locations


class TestFileInput:
    """Test parsing from file"""
    
    def test_parse_gcc_warnings_file(self):
        """Test parsing GCC warnings sample file"""
        sample_file = Path(__file__).parent / "samples" / "gcc_warnings.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        assert stats.files_compiled > 0
        assert stats.warnings > 0
        assert len(issues) > 0
    
    def test_parse_clang_errors_file(self):
        """Test parsing Clang errors sample file"""
        sample_file = Path(__file__).parent / "samples" / "clang_errors.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        assert stats.files_compiled > 0
        assert stats.warnings > 0
        assert stats.errors > 0
        assert return_code == 1  # Should fail because of errors
    
    def test_parse_avr_gcc_file(self):
        """Test parsing AVR-GCC build output"""
        sample_file = Path(__file__).parent / "samples" / "avr_gcc_build.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        assert stats.files_compiled > 0
        assert stats.warnings > 0
    
    def test_parse_qt_moc_file(self):
        """Test parsing Qt MOC build output"""
        sample_file = Path(__file__).parent / "samples" / "qt_moc_build.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        assert stats.moc_generated > 0
        assert stats.warnings > 0
    
    def test_parse_multiple_errors_file(self):
        """Test parsing file with multiple errors"""
        sample_file = Path(__file__).parent / "samples" / "gcc_multiple_errors.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        assert stats.errors >= 3
        assert stats.warnings > 0
        assert return_code == 1


class TestBuildIssue:
    """Test BuildIssue dataclass"""
    
    def test_issue_equality(self):
        """Test that issues with same type, message, and category are equal"""
        issue1 = BuildIssue(
            type="warning",
            file="file1.cpp",
            line=10,
            column=5,
            message="unused parameter",
            category="-Wunused-parameter"
        )
        
        issue2 = BuildIssue(
            type="warning",
            file="file2.cpp",  # Different file
            line=20,            # Different line
            column=10,          # Different column
            message="unused parameter",
            category="-Wunused-parameter"
        )
        
        # Should be equal for grouping purposes
        assert issue1 == issue2
        assert hash(issue1) == hash(issue2)
    
    def test_issue_inequality(self):
        """Test that issues with different messages are not equal"""
        issue1 = BuildIssue(
            type="warning",
            file="file.cpp",
            line=10,
            column=5,
            message="unused parameter",
            category="-Wunused-parameter"
        )
        
        issue2 = BuildIssue(
            type="warning",
            file="file.cpp",
            line=10,
            column=5,
            message="unused variable",
            category="-Wunused-variable"
        )
        
        assert issue1 != issue2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

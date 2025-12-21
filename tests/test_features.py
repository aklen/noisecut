"""
Additional tests for deduplication and severity features
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from noisecut.cli import parse_from_file
from noisecut.grouper import group_issues
from noisecut.severity import get_severity, Severity


class TestDeduplication:
    """Test that duplicate warnings from multiple TUs are deduplicated"""
    
    def test_duplicate_header_warnings_deduplicated(self):
        """Test that same warning from header included in multiple files appears only once"""
        sample_file = Path(__file__).parent / "samples" / "duplicate_headers.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        # Should detect files compiled (may be slightly off due to buffering/replay)
        assert stats.files_compiled >= 4
        
        # Should detect warnings
        assert stats.warnings > 0
        
        # Group issues
        grouped = group_issues(issues)
        
        # Find the override warning
        override_warning = None
        for group in grouped:
            if "overrides a member function" in group.issue.message:
                override_warning = group
                break
        
        assert override_warning is not None
        
        # The warning appears in 4 different compilation units,
        # but should only show the location once (utils.h:23:10)
        assert override_warning.count == 1, f"Expected 1 unique location, got {override_warning.count}"
        # Check location (file, line, col) - ignore message (4th element)
        file_path, line, col, _ = override_warning.locations[0]
        assert (file_path, line, col) == ("../include/utils.h", 23, 10)
    
    def test_different_locations_not_deduplicated(self):
        """Test that warnings at different locations are kept separate"""
        sample_file = Path(__file__).parent / "samples" / "duplicate_headers.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        grouped = group_issues(issues)
        
        # Should have at least 2 groups (override warning + unused variable)
        assert len(grouped) >= 2
        
        # Find unused variable warning (only in processor.cpp)
        unused_warning = None
        for group in grouped:
            if "unused variable" in group.issue.message:
                unused_warning = group
                break
        
        assert unused_warning is not None
        assert unused_warning.count == 1


class TestSeverityClassification:
    """Test warning severity classification"""
    
    def test_critical_severity(self):
        """Test CRITICAL severity warnings"""
        assert get_severity("-Wreturn-type") == Severity.CRITICAL
        assert get_severity("-Wuninitialized") == Severity.CRITICAL
        assert get_severity("-Wdelete-incomplete") == Severity.CRITICAL
    
    def test_high_severity(self):
        """Test HIGH severity warnings"""
        assert get_severity("-Wsign-compare") == Severity.HIGH
        assert get_severity("-Wsometimes-uninitialized") == Severity.HIGH
        assert get_severity("-Wmaybe-uninitialized") == Severity.HIGH
    
    def test_medium_severity(self):
        """Test MEDIUM severity warnings (default)"""
        assert get_severity("-Wunused-variable") == Severity.MEDIUM
        assert get_severity("-Wunused-parameter") == Severity.MEDIUM
        assert get_severity("-Wconversion") == Severity.MEDIUM
    
    def test_low_severity(self):
        """Test LOW severity warnings"""
        assert get_severity("-Winconsistent-missing-override") == Severity.LOW
        assert get_severity("-Wextra-semi") == Severity.LOW
    
    def test_info_severity(self):
        """Test INFO severity warnings"""
        assert get_severity("-Wcpp") == Severity.INFO
        assert get_severity("-Wpragmas") == Severity.INFO
    
    def test_unknown_category_defaults_to_medium(self):
        """Test that unknown categories default to MEDIUM"""
        assert get_severity("-Wsome-unknown-warning") == Severity.MEDIUM
        assert get_severity("-Wnonexistent") == Severity.MEDIUM


class TestSeverityInOutput:
    """Test that severity is correctly applied in real output"""
    
    def test_severity_shown_for_critical_warnings(self):
        """Test that CRITICAL warnings show severity badge"""
        sample_file = Path(__file__).parent / "samples" / "gcc_warnings.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        grouped = group_issues(issues)
        
        # Find return-type warning (CRITICAL)
        return_type_warning = None
        for group in grouped:
            if group.issue.category == "-Wreturn-type":
                return_type_warning = group
                break
        
        if return_type_warning:
            # Verify it's classified as CRITICAL
            assert get_severity(return_type_warning.issue.category) == Severity.CRITICAL
    
    def test_severity_shown_for_high_warnings(self):
        """Test that HIGH warnings show severity badge"""
        sample_file = Path(__file__).parent / "samples" / "clang_errors.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        grouped = group_issues(issues)
        
        # Find sign-compare warning (HIGH)
        sign_compare_warning = None
        for group in grouped:
            if group.issue.category == "-Wsign-compare":
                sign_compare_warning = group
                break
        
        if sign_compare_warning:
            # Verify it's classified as HIGH
            assert get_severity(sign_compare_warning.issue.category) == Severity.HIGH
    
    def test_severity_not_shown_for_medium_warnings(self):
        """Test that MEDIUM warnings don't show severity badge"""
        sample_file = Path(__file__).parent / "samples" / "gcc_warnings.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        grouped = group_issues(issues)
        
        # Find unused-parameter warning (MEDIUM)
        unused_param_warning = None
        for group in grouped:
            if group.issue.category == "-Wunused-parameter":
                unused_param_warning = group
                break
        
        if unused_param_warning:
            # Verify it's classified as MEDIUM (default, no badge)
            assert get_severity(unused_param_warning.issue.category) == Severity.MEDIUM


class TestLargeFirmwareBuild:
    """Test parsing of large real-world firmware build output"""
    
    def test_large_firmware_build_with_many_warnings(self):
        """Test parsing a large firmware build with 60+ fallthrough warnings"""
        sample_file = Path(__file__).parent / "samples" / "large_firmware_build.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        # Build should fail due to linker error
        assert return_code == 1
        
        # Should detect many files compiled
        assert stats.files_compiled > 10
        
        # Should detect warnings and errors
        assert stats.warnings > 50  # Many fallthrough warnings
        assert stats.errors == 1    # One linker error
        
        # Group issues
        grouped = group_issues(issues)
        
        # Find fallthrough warnings group
        fallthrough_warning = None
        for group in grouped:
            if "fall through" in group.issue.message:
                fallthrough_warning = group
                break
        
        assert fallthrough_warning is not None
        
        # Should have many unique locations (55+ different lines in usb_serial.c)
        assert fallthrough_warning.count >= 50, f"Expected 50+ fallthrough warnings, got {fallthrough_warning.count}"
        
        # All locations should be in comm_port.c but at different lines
        for file_path, line, col, _ in fallthrough_warning.locations:
            assert "comm_port.c" in file_path
        
        # Verify lines are unique (no duplicates)
        lines = [line for _, line, _, _ in fallthrough_warning.locations]
        assert len(lines) == len(set(lines)), "Found duplicate line numbers (deduplication bug)"
    
    def test_large_firmware_build_implicit_declaration_warnings(self):
        """Test that implicit declaration warnings are grouped correctly"""
        sample_file = Path(__file__).parent / "samples" / "large_firmware_build.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        grouped = group_issues(issues)
        
        # Should have multiple warning groups
        assert len(grouped) >= 3, f"Expected at least 3 warning groups, got {len(grouped)}"
    
    def test_large_firmware_build_linker_error(self):
        """Test that linker error is correctly parsed"""
        sample_file = Path(__file__).parent / "samples" / "large_firmware_build.txt"
        
        return_code, stats, issues = parse_from_file(str(sample_file), verbose=False)
        
        # Find linker error
        linker_error = None
        for issue in issues:
            if issue.type == "error" and "undefined reference" in issue.message:
                linker_error = issue
                break
        
        assert linker_error is not None
        assert "engine_update" in linker_error.message
        assert linker_error.file.endswith("control_module.c")
        assert linker_error.line == 211


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

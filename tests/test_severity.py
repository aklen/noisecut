#!/usr/bin/env python3
"""
Tests for severity classification
"""

import pytest
from noisecut.severity import (
    Severity, 
    SEVERITY_MAP, 
    get_severity, 
    get_severity_color
)


class TestSeverityConstants:
    """Tests for Severity class constants"""
    
    def test_severity_levels_are_unique(self):
        """Each severity level should be unique"""
        levels = [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO
        ]
        assert len(levels) == len(set(levels))
    
    def test_severity_levels_are_strings(self):
        """Severity levels should be uppercase strings"""
        assert Severity.CRITICAL == "CRITICAL"
        assert Severity.HIGH == "HIGH"
        assert Severity.MEDIUM == "MEDIUM"
        assert Severity.LOW == "LOW"
        assert Severity.INFO == "INFO"


class TestSeverityMap:
    """Tests for SEVERITY_MAP configuration"""
    
    def test_critical_warnings_in_map(self):
        """Critical warnings should be mapped"""
        assert SEVERITY_MAP["-Wdelete-non-virtual-dtor"] == Severity.CRITICAL
        assert SEVERITY_MAP["-Wuninitialized"] == Severity.CRITICAL
        assert SEVERITY_MAP["-Wreturn-type"] == Severity.CRITICAL
        assert SEVERITY_MAP["-Warray-bounds"] == Severity.CRITICAL
    
    def test_high_warnings_in_map(self):
        """High severity warnings should be mapped"""
        assert SEVERITY_MAP["-Wsign-compare"] == Severity.HIGH
        assert SEVERITY_MAP["-Wformat"] == Severity.HIGH
        assert SEVERITY_MAP["-Wdivision-by-zero"] == Severity.HIGH
    
    def test_medium_warnings_in_map(self):
        """Medium severity warnings should be mapped"""
        assert SEVERITY_MAP["-Wunused-variable"] == Severity.MEDIUM
        assert SEVERITY_MAP["-Wunused-parameter"] == Severity.MEDIUM
        assert SEVERITY_MAP["-Wdeprecated-declarations"] == Severity.MEDIUM
    
    def test_low_warnings_in_map(self):
        """Low severity warnings should be mapped"""
        assert SEVERITY_MAP["-Wextra-semi"] == Severity.LOW
        assert SEVERITY_MAP["-Wc++20-extensions"] == Severity.LOW
        assert SEVERITY_MAP["-Wc++17-extensions"] == Severity.LOW
    
    def test_info_warnings_in_map(self):
        """Info severity warnings should be mapped"""
        assert SEVERITY_MAP["-Wcpp"] == Severity.INFO
        assert SEVERITY_MAP["-Wpragmas"] == Severity.INFO
    
    def test_map_has_minimum_entries(self):
        """SEVERITY_MAP should have at least 50 entries"""
        assert len(SEVERITY_MAP) >= 50


class TestGetSeverity:
    """Tests for get_severity function"""
    
    def test_exact_match(self):
        """Should return exact match for known categories"""
        assert get_severity("-Wunused-variable") == Severity.MEDIUM
        assert get_severity("-Wreturn-type") == Severity.CRITICAL
        assert get_severity("-Wsign-compare") == Severity.HIGH
    
    def test_category_with_equal_sign(self):
        """Should handle categories with = suffix"""
        assert get_severity("-Wimplicit-fallthrough=") == Severity.HIGH
        assert get_severity("-Wimplicit-fallthrough=3") == Severity.HIGH
    
    def test_category_with_value(self):
        """Should handle categories with =N values"""
        # Even if the exact form isn't in the map, should strip =N and match
        assert get_severity("-Wimplicit-fallthrough=5") == Severity.HIGH
    
    def test_unknown_category_returns_medium(self):
        """Unknown categories should default to MEDIUM"""
        assert get_severity("-Wunknown-warning") == Severity.MEDIUM
        assert get_severity("-Wmade-up-category") == Severity.MEDIUM
    
    def test_empty_category(self):
        """Empty category should return default MEDIUM"""
        assert get_severity("") == Severity.MEDIUM
    
    def test_category_without_dash_w(self):
        """Categories without -W prefix should return default"""
        assert get_severity("unused-variable") == Severity.MEDIUM
    
    def test_all_severity_levels_represented(self):
        """All severity levels should be used in the map"""
        severities = set(SEVERITY_MAP.values())
        assert Severity.CRITICAL in severities
        assert Severity.HIGH in severities
        assert Severity.MEDIUM in severities
        assert Severity.LOW in severities
        assert Severity.INFO in severities
    
    def test_cpp_extensions_are_low(self):
        """C++ extension warnings should be LOW severity"""
        assert get_severity("-Wc++20-extensions") == Severity.LOW
        assert get_severity("-Wc++17-extensions") == Severity.LOW
        assert get_severity("-Wc++14-extensions") == Severity.LOW
    
    def test_memory_issues_are_critical(self):
        """Memory-related issues should be CRITICAL"""
        assert get_severity("-Wuse-after-free") == Severity.CRITICAL
        assert get_severity("-Wreturn-stack-address") == Severity.CRITICAL
        assert get_severity("-Wnull-dereference") == Severity.CRITICAL


class TestGetSeverityColor:
    """Tests for get_severity_color function"""
    
    def test_critical_has_color(self):
        """CRITICAL should return a color code"""
        color = get_severity_color(Severity.CRITICAL)
        assert isinstance(color, str)
        assert len(color) > 0
        assert '\033[' in color  # ANSI escape sequence
    
    def test_high_has_color(self):
        """HIGH should return a color code"""
        color = get_severity_color(Severity.HIGH)
        assert isinstance(color, str)
        assert '\033[' in color
    
    def test_medium_has_color(self):
        """MEDIUM should return a color code"""
        color = get_severity_color(Severity.MEDIUM)
        assert isinstance(color, str)
        assert '\033[' in color
    
    def test_low_has_color(self):
        """LOW should return a color code"""
        color = get_severity_color(Severity.LOW)
        assert isinstance(color, str)
        assert '\033[' in color
    
    def test_info_has_color(self):
        """INFO should return a color code"""
        color = get_severity_color(Severity.INFO)
        assert isinstance(color, str)
        assert '\033[' in color
    
    def test_critical_and_high_different(self):
        """CRITICAL and HIGH should have different colors"""
        critical_color = get_severity_color(Severity.CRITICAL)
        high_color = get_severity_color(Severity.HIGH)
        assert critical_color != high_color
    
    def test_unknown_severity_has_default(self):
        """Unknown severity should return default color"""
        color = get_severity_color("UNKNOWN")
        assert isinstance(color, str)
        assert '\033[' in color

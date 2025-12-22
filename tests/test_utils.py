#!/usr/bin/env python3
"""
Tests for utility functions
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from noisecut.utils import Color, get_terminal_width, format_location


class TestColor:
    """Tests for Color class constants"""
    
    def test_color_constants_are_strings(self):
        """All color constants should be strings"""
        assert isinstance(Color.RED, str)
        assert isinstance(Color.GREEN, str)
        assert isinstance(Color.YELLOW, str)
        assert isinstance(Color.BLUE, str)
        assert isinstance(Color.CYAN, str)
        assert isinstance(Color.MAGENTA, str)
        assert isinstance(Color.BOLD, str)
        assert isinstance(Color.DIM, str)
        assert isinstance(Color.NC, str)
    
    def test_color_codes_start_with_escape(self):
        """ANSI color codes should start with escape sequence"""
        assert Color.RED.startswith('\033[')
        assert Color.GREEN.startswith('\033[')
        assert Color.YELLOW.startswith('\033[')
        assert Color.BLUE.startswith('\033[')
        assert Color.CYAN.startswith('\033[')
        assert Color.MAGENTA.startswith('\033[')
        assert Color.BOLD.startswith('\033[')
        assert Color.DIM.startswith('\033[')
        assert Color.NC.startswith('\033[')
    
    def test_color_codes_end_with_m(self):
        """ANSI color codes should end with 'm'"""
        assert Color.RED.endswith('m')
        assert Color.GREEN.endswith('m')
        assert Color.YELLOW.endswith('m')
        assert Color.BLUE.endswith('m')
        assert Color.CYAN.endswith('m')
        assert Color.MAGENTA.endswith('m')
        assert Color.BOLD.endswith('m')
        assert Color.DIM.endswith('m')
        assert Color.NC.endswith('m')
    
    def test_reset_code(self):
        """NC (No Color) should be the reset code"""
        assert Color.NC == '\033[0m'


class TestGetTerminalWidth:
    """Tests for get_terminal_width function"""
    
    def test_returns_positive_integer(self):
        """Should always return a positive integer"""
        width = get_terminal_width()
        assert isinstance(width, int)
        assert width > 0
    
    def test_default_parameter(self):
        """Should use default parameter when terminal size unavailable"""
        with patch('shutil.get_terminal_size', return_value=os.terminal_size((100, 20))):
            width = get_terminal_width(default=100)
            assert width == 100
    
    def test_custom_default(self):
        """Should respect custom default value"""
        with patch('shutil.get_terminal_size', return_value=os.terminal_size((120, 20))):
            width = get_terminal_width(default=120)
            assert width == 120
    
    def test_minimum_width(self):
        """Width should be at least 1"""
        with patch('shutil.get_terminal_size', return_value=os.terminal_size((1, 20))):
            width = get_terminal_width(default=1)
            assert width >= 1
    
    def test_standard_default_is_80(self):
        """Standard default should be 80 columns"""
        # If no default specified, function uses 80
        with patch('shutil.get_terminal_size') as mock:
            mock.return_value = os.terminal_size((80, 20))
            width = get_terminal_width()
            # Verify the function called get_terminal_size with (80, 20)
            mock.assert_called_once_with((80, 20))


class TestFormatLocation:
    """Tests for format_location function"""
    
    def test_simple_path(self):
        """Format simple file path with line and column"""
        result = format_location("main.cpp", 42, 10)
        assert result == "main.cpp:42:10"
    
    def test_absolute_path(self):
        """Format absolute path with line and column"""
        result = format_location("/usr/src/app/main.cpp", 100, 5)
        assert result == "/usr/src/app/main.cpp:100:5"
    
    def test_relative_path(self):
        """Format relative path with line and column"""
        result = format_location("../../src/utils.cpp", 25, 8)
        assert result == "../../src/utils.cpp:25:8"
    
    def test_line_number_one(self):
        """Format with line number 1"""
        result = format_location("test.c", 1, 1)
        assert result == "test.c:1:1"
    
    def test_large_line_numbers(self):
        """Format with large line and column numbers"""
        result = format_location("bigfile.cpp", 9999, 500)
        assert result == "bigfile.cpp:9999:500"
    
    def test_zero_column(self):
        """Format with column 0 (some compilers use 0-based columns)"""
        result = format_location("file.h", 50, 0)
        assert result == "file.h:50:0"
    
    def test_spaces_in_path(self):
        """Format path with spaces"""
        result = format_location("my project/src/main.cpp", 10, 5)
        assert result == "my project/src/main.cpp:10:5"
    
    def test_windows_path(self):
        """Format Windows-style path"""
        result = format_location("C:\\Users\\dev\\project\\main.cpp", 42, 10)
        assert result == "C:\\Users\\dev\\project\\main.cpp:42:10"
    
    def test_format_consistency(self):
        """Verify consistent colon-separated format"""
        result = format_location("file.cpp", 10, 20)
        parts = result.split(':')
        assert len(parts) == 3
        assert parts[0] == "file.cpp"
        assert parts[1] == "10"
        assert parts[2] == "20"

"""
Tests for path normalization functionality
"""

import pytest
from noisecut.grouper import normalize_path_for_dedup


class TestPathNormalization:
    """Test path normalization for deduplication"""
    
    def test_simple_relative_path(self):
        """Test simple relative path with parent references"""
        result = normalize_path_for_dedup("../../src/main.cpp")
        assert result == "src/main.cpp"
    
    def test_single_parent_reference(self):
        """Test path with single parent reference"""
        result = normalize_path_for_dedup("../drivers/gps/sensor.cpp")
        assert result == "drivers/gps/sensor.cpp"
    
    def test_absolute_path(self):
        """Test absolute path - should return last 3 components"""
        result = normalize_path_for_dedup("/home/user/project/src/window/main.cpp")
        assert result == "src/window/main.cpp"
    
    def test_path_with_moc_directory(self):
        """Test path containing moc directory (should be filtered)"""
        result = normalize_path_for_dedup("moc/../../src/window/widget.cpp")
        assert result == "src/window/widget.cpp"
    
    def test_path_with_build_directory(self):
        """Test path containing build directory (should be filtered)"""
        result = normalize_path_for_dedup("build/../src/util/helper.cpp")
        assert result == "src/util/helper.cpp"
    
    def test_path_with_obj_directory(self):
        """Test path containing obj directory (should be filtered)"""
        result = normalize_path_for_dedup("obj/../../src/core/engine.cpp")
        assert result == "src/core/engine.cpp"
    
    def test_complex_relative_path(self):
        """Test complex path with multiple parent and build dirs"""
        result = normalize_path_for_dedup("moc/../../build/obj/../src/window/tab.cpp")
        assert result == "src/window/tab.cpp"
    
    def test_windows_path_separators(self):
        """Test Windows-style backslash separators"""
        result = normalize_path_for_dedup(r"..\..\src\window\main.cpp")
        assert result == "src/window/main.cpp"
    
    def test_mixed_separators(self):
        """Test mixed forward and backslash separators"""
        result = normalize_path_for_dedup(r"../../src\window/main.cpp")
        assert result == "src/window/main.cpp"
    
    def test_short_path_less_than_3_components(self):
        """Test path with less than 3 components - should return all"""
        result = normalize_path_for_dedup("src/main.cpp")
        assert result == "src/main.cpp"
    
    def test_single_component_path(self):
        """Test path with single component"""
        result = normalize_path_for_dedup("main.cpp")
        assert result == "main.cpp"
    
    def test_preserves_file_in_different_directories(self):
        """Test that same filename in different dirs are distinct"""
        path1 = normalize_path_for_dedup("../../src/utils/logger.cpp")
        path2 = normalize_path_for_dedup("../../src/drivers/logger.cpp")
        assert path1 == "src/utils/logger.cpp"
        assert path2 == "src/drivers/logger.cpp"
        assert path1 != path2
    
    def test_same_file_different_paths(self):
        """Test that different relative paths to same file are normalized to same"""
        path1 = normalize_path_for_dedup("../../src/window/EMainTab/emaintab.h")
        path2 = normalize_path_for_dedup("../src/window/EMainTab/emaintab.h")
        path3 = normalize_path_for_dedup("moc/../../src/window/EMainTab/emaintab.h")
        
        assert path1 == "window/EMainTab/emaintab.h"
        assert path2 == "window/EMainTab/emaintab.h"
        assert path3 == "window/EMainTab/emaintab.h"
        assert path1 == path2 == path3
    
    def test_deep_nested_path(self):
        """Test very deep nested path"""
        result = normalize_path_for_dedup("../../../../../../../src/module/component/file.cpp")
        assert result == "module/component/file.cpp"
    
    def test_current_directory_references(self):
        """Test path with current directory (.) references"""
        result = normalize_path_for_dedup("./src/./window/./main.cpp")
        assert result == "src/window/main.cpp"
    
    def test_empty_parts_filtered(self):
        """Test that empty path parts are filtered"""
        result = normalize_path_for_dedup("src//window///main.cpp")
        assert result == "src/window/main.cpp"
    
    def test_out_directory_filtered(self):
        """Test that 'out' directory is filtered"""
        result = normalize_path_for_dedup("out/../src/window/main.cpp")
        assert result == "src/window/main.cpp"
    
    def test_header_file(self):
        """Test with header file extension"""
        result = normalize_path_for_dedup("../../include/common/config.h")
        assert result == "include/common/config.h"
    
    def test_qt_moc_generated_path(self):
        """Test typical Qt MOC generated file path"""
        result = normalize_path_for_dedup("moc/../../src/window/EMainTab/emaintab.h")
        assert result == "window/EMainTab/emaintab.h"
    
    def test_preserves_extension(self):
        """Test that file extension is preserved"""
        cpp_result = normalize_path_for_dedup("../../src/main.cpp")
        h_result = normalize_path_for_dedup("../../src/main.h")
        assert cpp_result == "src/main.cpp"
        assert h_result == "src/main.h"
        assert cpp_result != h_result

#!/usr/bin/env python3
"""
Tests for .NET/MSBuild parser
"""

import pytest
from noisecut.parsers.dotnet import DotNetParser
from noisecut.model import BuildIssue


class TestDotNetParser:
    """Tests for DotNetParser"""
    
    def test_parse_cs_warning(self):
        """Should parse C# compiler warning"""
        parser = DotNetParser()
        line = "/Users/user/project/File.cs(76,34): warning CS0168: The variable 'ex' is declared but never used"
        
        issue = parser.parse_line(line)
        
        assert issue is not None
        assert issue.type == "warning"
        assert issue.file == "/Users/user/project/File.cs"
        assert issue.line == 76
        assert issue.column == 34
        assert issue.category == "-WCS0168"
        assert "variable" in issue.message.lower()
        assert "never used" in issue.message.lower()
    
    def test_parse_nullability_warning(self):
        """Should parse nullable reference warning"""
        parser = DotNetParser()
        line = "/path/to/File.cs(310,13): warning CS8602: Dereference of a possibly null reference."
        
        issue = parser.parse_line(line)
        
        assert issue is not None
        assert issue.type == "warning"
        assert issue.line == 310
        assert issue.column == 13
        assert issue.category == "-WCS8602"
        assert "null reference" in issue.message.lower()
    
    def test_parse_syslib_warning(self):
        """Should parse SYSLIB obsolete API warning"""
        parser = DotNetParser()
        line = "/path/File.cs(51,16): warning SYSLIB0057: 'X509Certificate2.X509Certificate2(byte[], string?, X509KeyStorageFlags)' is obsolete: 'Loading certificate data through the constructor or Import is obsolete. Use X509CertificateLoader instead to load certificates.' (https://aka.ms/dotnet-warnings/SYSLIB0057)"
        
        issue = parser.parse_line(line)
        
        assert issue is not None
        assert issue.type == "warning"
        assert issue.category == "-WSYSLIB0057"
        assert "obsolete" in issue.message.lower()
        # URL should be stripped from message
        assert "https://" not in issue.message
    
    def test_parse_analyzer_warning(self):
        """Should parse third-party analyzer warning (e.g., MsgPack)"""
        parser = DotNetParser()
        line = "/path/Replica.cs(36,37): warning MsgPack017: The value of a property with an init accessor and an initializer will be reset to the default value for the type upon deserialization when no value for them is deserialized (https://github.com/MessagePack-CSharp/MessagePack-CSharp/blob/master/doc/analyzers/MsgPack017.md)"
        
        issue = parser.parse_line(line)
        
        assert issue is not None
        assert issue.type == "warning"
        assert issue.category == "-WMsgPack017"
        assert "property" in issue.message.lower()
        # GitHub URL should be stripped
        assert "github.com" not in issue.message
    
    def test_parse_error(self):
        """Should parse C# compiler error"""
        parser = DotNetParser()
        line = "/path/File.cs(42,10): error CS0103: The name 'foo' does not exist in the current context"
        
        issue = parser.parse_line(line)
        
        assert issue is not None
        assert issue.type == "error"
        assert issue.line == 42
        assert issue.column == 10
        assert issue.category == "-WCS0103"
    
    def test_parse_build_success(self):
        """Should track build success lines"""
        parser = DotNetParser()
        line = "  Ape.Core net9.0 succeeded with 3 warning(s) (1.7s) → build/bin/Ape.Core/Debug/net9.0/Ape.Core.dll"
        
        issue = parser.parse_line(line)
        
        assert issue is None  # Not an issue, just tracking
        assert parser.stats.files_compiled == 1
    
    def test_parse_restore_complete(self):
        """Should handle restore complete lines"""
        parser = DotNetParser()
        line = "Restore complete (1.2s)"
        
        issue = parser.parse_line(line)
        
        assert issue is None
    
    def test_detect_dotnet_output(self):
        """Should detect .NET build output"""
        lines = [
            "Restore complete (1.2s)",
            "  Ape.Core net9.0 succeeded (1.7s)",
            "/path/File.cs(76,34): warning CS0168: Variable unused",
            "Build succeeded with 1 warning(s) in 2.0s"
        ]
        
        assert DotNetParser.detect(lines) is True
    
    def test_detect_not_dotnet(self):
        """Should not detect non-.NET output"""
        lines = [
            "gcc -c main.c",
            "main.c:10:5: warning: unused variable 'x' [-Wunused-variable]",
            "make: *** [build] Error 1"
        ]
        
        assert DotNetParser.detect(lines) is False
    
    def test_stats_tracking(self):
        """Should track warnings and errors"""
        parser = DotNetParser()
        
        parser.parse_line("/path/File.cs(10,5): warning CS0168: Variable unused")
        parser.parse_line("/path/File.cs(20,5): warning CS0414: Field unused")
        parser.parse_line("/path/File.cs(30,5): error CS0103: Name does not exist")
        
        assert parser.stats.warnings == 2
        assert parser.stats.errors == 1
        assert len(parser.issues) == 3
    
    def test_windows_path(self):
        """Should handle Windows-style paths"""
        parser = DotNetParser()
        line = r"C:\Users\user\project\File.cs(76,34): warning CS0168: Variable unused"
        
        issue = parser.parse_line(line)
        
        assert issue is not None
        assert issue.file == r"C:\Users\user\project\File.cs"
    
    def test_relative_path(self):
        """Should handle relative paths"""
        parser = DotNetParser()
        line = "src/Services/Manager.cs(10,5): warning CS0168: Variable unused"
        
        issue = parser.parse_line(line)
        
        assert issue is not None
        assert issue.file == "src/Services/Manager.cs"
    
    def test_finalize(self):
        """Should have finalize method"""
        parser = DotNetParser()
        parser.parse_line("/path/File.cs(10,5): warning CS0168: Variable unused")
        
        # Should not crash
        parser.finalize()
        
        assert len(parser.issues) == 1

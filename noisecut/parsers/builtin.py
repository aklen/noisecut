"""
Register all built-in compilers

This module imports all parser implementations and registers them
in the central registry. To add a new compiler:

1. Implement YourParser(BaseParser) in parsers/your_compiler.py
2. Import it here
3. Call register_compiler() with metadata

That's it! Auto-detection will work automatically.
"""

from .registry import register_compiler
from .gcc import GccParser
from .clang import ClangParser
from .avr_gcc import AvrGccParser
from .dotnet import DotNetParser


def register_all_compilers():
    """Register all built-in compiler parsers"""
    
    # GCC (GNU C/C++ Compiler)
    register_compiler(
        key='gcc',
        name='GNU C/C++ Compiler',
        parser_class=GccParser,
        extensions=['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'],
        project_files=['Makefile', 'GNUmakefile', 'makefile', 'CMakeLists.txt'],
        detection_keywords=['gcc', 'g++', 'gnu', 'Building CXX object'],
        command_patterns=['gcc', 'g++', '/usr/bin/gcc', '/usr/bin/g++']
    )
    
    # Clang (LLVM C/C++ Compiler)
    register_compiler(
        key='clang',
        name='Clang/LLVM C/C++ Compiler',
        parser_class=ClangParser,
        extensions=['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp'],
        project_files=['CMakeLists.txt', 'Makefile'],
        detection_keywords=['clang', 'clang++', 'llvm', 'Building CXX object'],
        command_patterns=['clang', 'clang++', '/usr/bin/clang', '/usr/bin/clang++']
    )
    
    # AVR-GCC (AVR Microcontroller Compiler)
    register_compiler(
        key='avr-gcc',
        name='AVR-GCC Microcontroller Compiler',
        parser_class=AvrGccParser,
        extensions=['.c', '.cpp', '.h', '.hpp'],
        project_files=['Makefile', 'avr-makefile'],
        detection_keywords=['avr-gcc', 'avr-g++', 'avr'],
        command_patterns=['avr-gcc', 'avr-g++']
    )
    
    # .NET/MSBuild (C# Compiler)
    register_compiler(
        key='dotnet',
        name='.NET/MSBuild C# Compiler',
        parser_class=DotNetParser,
        extensions=['.cs', '.csproj', '.sln'],
        project_files=['*.csproj', '*.sln', 'Directory.Build.props'],
        detection_keywords=['dotnet', 'msbuild', 'csc', 'net9.0', 'net8.0', 'net7.0'],
        command_patterns=['dotnet', 'msbuild', 'csc']
    )


# Auto-register on import
register_all_compilers()

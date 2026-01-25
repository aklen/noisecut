"""
Compiler registry and metadata

Central registry for all supported compilers with metadata for auto-detection.
Adding a new compiler requires only registering it here + implementing the parser.
"""

from typing import Dict, Type, List, Optional
from dataclasses import dataclass
from .base import BaseParser


@dataclass
class CompilerMetadata:
    """Metadata for compiler detection and identification"""
    name: str                           # Human-readable name
    parser_class: Type[BaseParser]      # Parser class to instantiate
    extensions: List[str]               # File extensions (.c, .cpp, .cs)
    project_files: List[str]            # Project file patterns (Makefile, *.csproj)
    detection_keywords: List[str]       # Keywords in output (gcc, clang, dotnet build)
    command_patterns: List[str]         # Command line patterns (gcc, g++, clang++)


# Registry of all supported compilers
COMPILER_REGISTRY: Dict[str, CompilerMetadata] = {}


def register_compiler(
    key: str,
    name: str,
    parser_class: Type[BaseParser],
    extensions: List[str] = None,
    project_files: List[str] = None,
    detection_keywords: List[str] = None,
    command_patterns: List[str] = None
) -> None:
    """
    Register a compiler in the registry.
    
    Args:
        key: Unique identifier (e.g., 'gcc', 'clang', 'dotnet')
        name: Human-readable name
        parser_class: Parser class (e.g., GccParser)
        extensions: File extensions this compiler handles
        project_files: Project file patterns for detection
        detection_keywords: Keywords to detect in build output
        command_patterns: Command line patterns to detect
    """
    COMPILER_REGISTRY[key] = CompilerMetadata(
        name=name,
        parser_class=parser_class,
        extensions=extensions or [],
        project_files=project_files or [],
        detection_keywords=detection_keywords or [],
        command_patterns=command_patterns or []
    )


def get_parser(compiler_key: str) -> BaseParser:
    """
    Get parser instance for a compiler.
    
    Args:
        compiler_key: Compiler identifier from registry
        
    Returns:
        Parser instance
        
    Raises:
        KeyError: If compiler not registered
    """
    if compiler_key not in COMPILER_REGISTRY:
        raise KeyError(f"Compiler '{compiler_key}' not registered. "
                      f"Available: {', '.join(COMPILER_REGISTRY.keys())}")
    
    metadata = COMPILER_REGISTRY[compiler_key]
    return metadata.parser_class()


def get_compiler_by_keyword(keyword: str) -> Optional[str]:
    """
    Find compiler by detection keyword.
    
    Args:
        keyword: Keyword to search for (e.g., 'gcc', 'dotnet')
        
    Returns:
        Compiler key or None
    """
    keyword_lower = keyword.lower()
    for key, metadata in COMPILER_REGISTRY.items():
        if any(kw.lower() in keyword_lower for kw in metadata.detection_keywords):
            return key
    return None


def get_compiler_by_project_files(project_files: List[str]) -> Optional[str]:
    """
    Find compiler by project file patterns.
    
    Args:
        project_files: List of project file names/patterns
        
    Returns:
        Compiler key or None
    """
    for key, metadata in COMPILER_REGISTRY.items():
        for project_file in project_files:
            if any(pattern in project_file for pattern in metadata.project_files):
                return key
    return None


def list_compilers() -> List[str]:
    """Get list of all registered compiler keys"""
    return list(COMPILER_REGISTRY.keys())


def get_compiler_info(compiler_key: str) -> Optional[CompilerMetadata]:
    """
    Get metadata for a compiler.
    
    Args:
        compiler_key: Compiler identifier
        
    Returns:
        CompilerMetadata or None
    """
    return COMPILER_REGISTRY.get(compiler_key)

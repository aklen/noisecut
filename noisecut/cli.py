"""
Command-line interface for noisecut
"""

import argparse
import subprocess
import sys
import os
import time
from typing import List, Tuple

from .model import BuildIssue, BuildStats
from .parsers.factory import create_parser, AutoDetectParser
from .parsers.registry import list_compilers
from .grouper import group_issues
from .reporter import print_issue_summary, print_build_stats
from .utils import Color

__version__ = "0.4.2"


def parse_from_file(file_path: str, verbose: bool = False, 
                    parser=None) -> Tuple[int, BuildStats, List[BuildIssue]]:
    """
    Parse compiler output from a file.
    
    Args:
        file_path: Path to the file containing compiler output
        verbose: If True, print all lines; if False, only formatted lines
        parser: Parser instance to use (defaults to AutoDetectParser)
        
    Returns:
        Tuple of (return_code, stats, issues)
    """
    if parser is None:
        parser = AutoDetectParser()
    
    start_time = time.time()
    
    print(f"{Color.BOLD}Parsing file:{Color.NC} {file_path}\n")
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.rstrip()
                
                # Parse line
                formatted = parser.parse_line(line)
                
                # Print if verbose or it's a formatted message
                if verbose:
                    print(line)
                elif formatted:
                    print(formatted)
        
        # Assume success if we could parse the file
        return_code = 0 if parser.stats.errors == 0 else 1
        
    except FileNotFoundError:
        print(f"{Color.RED}Error: File not found: {file_path}{Color.NC}")
        return 1, parser.stats, []
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}Parsing interrupted{Color.NC}")
        return 130, parser.stats, []
    
    parser.finalize()
    parser.stats.duration = time.time() - start_time
    
    return return_code, parser.stats, parser.issues


def run_build(command: List[str], verbose: bool = False,
              parser=None) -> Tuple[int, BuildStats, List[BuildIssue]]:
    """
    Run build command and parse output.
    
    Args:
        command: Command to execute (e.g., ['make', '-j8'])
        verbose: If True, print all lines; if False, only formatted lines
        parser: Parser instance to use (defaults to AutoDetectParser)
        
    Returns:
        Tuple of (return_code, stats, issues)
    """
    if parser is None:
        parser = AutoDetectParser()
    
    start_time = time.time()
    
    print(f"{Color.BOLD}Running:{Color.NC} {' '.join(command)}\n")
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            line = line.rstrip()
            
            # Parse line
            formatted = parser.parse_line(line)
            
            # Print if verbose or it's a formatted message
            if verbose:
                print(line)
            elif formatted:
                print(formatted)
        
        return_code = process.wait()
        
    except FileNotFoundError:
        print(f"{Color.RED}Error: Command not found: {command[0]}{Color.NC}")
        return 1, parser.stats, []
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}Build interrupted{Color.NC}")
        process.kill()
        return 130, parser.stats, []
    
    parser.finalize()
    parser.stats.duration = time.time() - start_time
    
    return return_code, parser.stats, parser.issues


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description=f'Build output analyzer for C/C++/.NET projects (v{__version__})',
        prog='ncut'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show all compiler output (not just summary)'
    )
    parser.add_argument(
        '-f', '--file',
        type=str,
        metavar='FILE',
        help='Parse compiler output from file instead of running build'
    )
    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=8,
        help='Number of parallel jobs (default: 8)'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean before building'
    )
    parser.add_argument(
        '--max-locations',
        type=int,
        default=5,
        help='Maximum locations to show per issue (default: 5)'
    )
    parser.add_argument(
        '--no-severity',
        action='store_true',
        help='Disable severity level display for warnings'
    )
    
    # Dynamically get available compilers from registry
    available_compilers = ['auto'] + list_compilers()
    parser.add_argument(
        '--parser',
        type=str,
        choices=available_compilers,
        default='auto',
        help='Parser to use (default: auto-detect)'
    )
    parser.add_argument(
        'target',
        nargs='?',
        default=None,
        help='Make target (default: all)'
    )
    
    args = parser.parse_args()
    
    # Select parser
    if args.parser == 'auto':
        parser_instance = AutoDetectParser()
    else:
        parser_instance = create_parser(args.parser)
    
    # Parse from file if specified
    if args.file:
        return_code, stats, issues = parse_from_file(
            args.file, args.verbose, parser_instance
        )
    else:
        # Change to build directory if not already there
        if not os.path.exists('Makefile'):
            if os.path.exists('build/Makefile'):
                os.chdir('build')
                print(f"{Color.CYAN}Changed to build directory{Color.NC}\n")
            else:
                print(f"{Color.RED}Error: No Makefile found. Run qmake first.{Color.NC}")
                return 1
        
        # Clean if requested
        if args.clean:
            print(f"{Color.YELLOW}Cleaning...{Color.NC}")
            subprocess.run(['make', 'clean'], capture_output=True)
            print()
        
        # Build command
        command = ['make', f'-j{args.jobs}']
        if args.target:
            command.append(args.target)
        
        # Run build
        return_code, stats, issues = run_build(
            command, args.verbose, parser_instance
        )
    
    # Print issues if any
    if issues:
        print(f"\n{Color.BOLD}{'=' * 60}{Color.NC}")
        print(f"{Color.BOLD}Issue Summary{Color.NC}")
        print(f"{Color.BOLD}{'=' * 60}{Color.NC}")
        
        grouped = group_issues(issues)
        print_issue_summary(grouped, args.max_locations, show_severity=not args.no_severity)
    
    # Print statistics
    print_build_stats(stats, return_code == 0)
    
    # Show detected parser if auto-detect was used
    if args.parser == 'auto' and isinstance(parser_instance, AutoDetectParser):
        if parser_instance.detected_parser:
            print(f"\n{Color.DIM}Auto-detected compiler: {parser_instance.detected_parser}{Color.NC}")
    
    # Exit with build return code
    return return_code


if __name__ == '__main__':
    sys.exit(main())

# noisecut

Cut through compiler noise. See what really matters.

A modular build output analyzer for C/C++ projects that transforms raw compiler output into clear, actionable insight.

**Keywords:** C++, C, build tools, compiler diagnostics, clang, gcc, build log analysis, warning aggregation, developer tooling, CI, command-line tools

## Overview

`noisecut` is a Python-based build analysis tool that parses GCC/Clang/AVR-GCC compiler output and provides:

- **Automatic compiler detection** - recognizes GCC, Clang, AVR-GCC automatically
- **Smart warning grouping** - groups warnings by category (e.g., all "unused parameter" warnings together)
- **Severity classification** - 5-level severity system (INFO, LOW, MEDIUM, HIGH, CRITICAL) with 50+ warning types classified
- **Severity-based sorting** - most critical issues appear at the bottom for immediate visibility
- **Colorized output** - severity badges color-coded (cyan for INFO/LOW, white for MEDIUM, red for HIGH/CRITICAL)
- **Build statistics** - tracks files compiled, warnings, errors, and duration
- **Modular architecture** - easily extensible with new parsers
- **Clean summary** - hides verbose compiler flags, shows only essentials

noisecut is not a linter or static analyzer — it works purely on compiler output and build logs.

## Features

### Automatic Compiler Detection

Smart multi-stage auto-detection with fallback mechanisms:
1. **Direct detection** from compilation commands (gcc, clang, avr-gcc)
2. **Project file inspection** (Makefile, CMakeLists.txt, PKGBUILD)
3. **Warning format analysis** (GCC vs Clang patterns)
4. **Buffering and replay** - stores first 100 lines, replays when compiler detected

Supports:
- GCC/G++
- Clang/Clang++
- AVR-GCC (for embedded systems)

No manual parser selection needed - just run and it figures it out!

### Intelligent Output Parsing

Parses diverse compiler output formats:
- Standard compilation commands (`gcc -c ... -o file.o`)
- Make-style bullet points (`• Compiling src/file.c`)
- MOC generation (`[MOC]`) for Qt projects
- Warnings and errors with file locations
- Linker errors (undefined references)
- Additional context (notes, overridden functions, etc.)
- Warning categories with optional values (e.g., `-Wimplicit-fallthrough=`)

### Smart Warning Grouping

Groups warnings by category, not individual messages:
- `unused parameter 'flags'` and `unused parameter 'argc'` → grouped as **"unused parameter"** (2 occurrences)
- Variable/function names shown in parentheses per location
- Category badge (e.g., `-Wunused-parameter`, `-Wimplicit-fallthrough=`)
- All file locations listed together
- Count of total occurrences

### Severity Classification

5-level severity system with 50+ warning types classified:

- **CRITICAL** - Memory corruption, undefined behavior (dangling pointers, return-type, infinite recursion)
- **HIGH** - Likely bugs (sign-compare, overflow, implicit-fallthrough, uninitialized variables)
- **MEDIUM** - Code quality (unused variables, unused parameters, shadowing)
- **LOW** - Style/cosmetic (missing override, extra semicolons)
- **INFO** - Informational (#warning directives, pragmas)

Warnings are **sorted by severity** - most critical issues appear at the **bottom** of the output, so you see them immediately without scrolling!

**Example output:**
```
⚠ WARNING [INFO]: #warning "Debug mode enabled"
⚠ WARNING [MEDIUM]: unused parameter (5 occurrences)
⚠ WARNING [HIGH]: implicit-fallthrough (63 occurrences)
⚠ WARNING [CRITICAL]: control reaches end of non-void function
✗ ERROR: undefined reference to 'main'
```

### Color Coding

- **Cyan**: Compilation info, `[INFO]` and `[LOW]` severity badges
- **Magenta**: MOC (Meta-Object Compiler) generation
- **Yellow**: All warnings (consistent color)
- **White**: `[MEDIUM]` severity badge
- **Red**: Errors, `[HIGH]` and `[CRITICAL]` severity badges (bold for CRITICAL)
- **Green**: Success status
- **Bold**: Important messages and critical severities

Colors are disabled automatically when:
- Output is redirected to a file
- Running in non-interactive mode
- `NO_COLOR` environment variable is set

## Installation

### Recommended: pipx (Isolated Install)

The easiest way to install `noisecut` globally is with [pipx](https://pipx.pypa.io/):

```bash
pipx install git+https://github.com/aklen/noisecut.git
```

This installs `noisecut` in an isolated environment and adds the `ncut` command to your PATH.

**Upgrade:**
```bash
pipx upgrade noisecut
```

**Uninstall:**
```bash
pipx uninstall noisecut
```

### Alternative: pip

You can also install with pip (user install):

```bash
pip install --user git+https://github.com/aklen/noisecut.git
```

### Development Install

For development, clone the repository and install in editable mode:

```bash
git clone https://github.com/aklen/noisecut.git
cd noisecut
pip install -e .
```

### No Install (Direct Usage)

No installation required. Simply ensure you have Python 3.7+ installed:

```bash
python3 --version
```

The package uses only standard library modules. Run directly with `./ncut.py` or `python -m noisecut`.

## Usage

### Parse Build Output from File

Parse compiler output that was saved to a file (auto-detects compiler):

```bash
./ncut.py -f build_output.txt
# or as Python module
python -m noisecut -f build_output.txt
```

This is useful for:
- Analyzing builds from CI/CD pipelines
- Reviewing historical build logs
- Testing and debugging the parser
- Sharing build analysis with team members

### Run Live Build

```bash
./ncut.py
# or as Python module
python -m noisecut
```

### Clean Build

```bash
./ncut.py --clean
```

### Parallel Build

```bash
./ncut.py -j 16
```

### Verbose Mode

Show all compiler output instead of just the summary:

```bash
./ncut.py -v
```

### Build Specific Target

```bash
./ncut.py mytarget
```

### Show More Locations Per Issue

```bash
./ncut.py --max-locations 10
```

### Disable Severity Classification

If you prefer the classic output without severity badges:

```bash
./ncut.py --no-severity
```

### Manual Parser Selection

By default, noisecut auto-detects the compiler. You can override this:

```bash
./ncut.py --parser gcc -f build_output.txt
./ncut.py --parser clang -f build_output.txt
./ncut.py --parser avr-gcc -f build_output.txt
```

## Command Line Options

```
usage: ncut [-h] [-v] [-f FILE] [-j JOBS] [--clean] [--max-locations MAX_LOCATIONS] 
            [--no-severity] [--parser {auto,gcc,clang,avr-gcc}] [target]

Build output analyzer for C/C++ projects

positional arguments:
  target                Make target (default: all)

optional arguments:
  -h, --help            Show this help message and exit
  -v, --verbose         Show all compiler output (not just summary)
  -f FILE, --file FILE  Parse compiler output from file instead of running build
  -j JOBS, --jobs JOBS  Number of parallel jobs (default: 8)
  --clean               Clean before building
  --max-locations MAX_LOCATIONS
                        Maximum locations to show per issue (default: 5)
  --no-severity         Disable severity classification badges
  --parser {auto,gcc,clang,avr-gcc}
                        Parser to use (default: auto-detect)
```

## Architecture

The project follows a modular architecture:

```
noisecut/
├── __init__.py          # Package exports
├── __main__.py          # python -m noisecut entry point
├── cli.py               # CLI logic and main()
├── model.py             # Data models (BuildIssue, BuildStats)
├── grouper.py           # Issue grouping logic
├── reporter.py          # Output formatting
├── utils.py             # Color codes and helpers
└── parsers/
    ├── base.py          # Abstract BaseParser
    ├── gcc.py           # GCC/G++ parser
    ├── clang.py         # Clang/Clang++ parser
    ├── avr_gcc.py       # AVR-GCC parser
    └── factory.py       # Auto-detection and parser factory
```

### Adding New Parsers

To add support for a new compiler:

1. Create a new parser in `noisecut/parsers/your_compiler.py`
2. Extend `BaseParser` class
3. Add detection logic in `factory.py`
4. Register in `parsers/__init__.py`

## Comparison with Standard Make Output

| Feature | `make -j8` | `ncut` |
|---------|-----------|--------|
| See compilation progress | Verbose flags | Clean summary |
| Group similar warnings | No | **Yes - by category** |
| Severity classification | No | **Yes - 5 levels** |
| Smart sorting | No | **Yes - critical at bottom** |
| Colorized output | No | **Yes - severity badges** |
| Build statistics | No | Yes |
| Error summary | Scattered | **Grouped at end** |
| Show all locations | Need to scroll | **Listed together** |
| Compiler detection | Manual | **Automatic multi-stage** |
| Multiple compilers | Single project | Mixed projects supported |
| Make-style output | N/A | **Parsed natively** |
| Linker errors | Mixed with output | **Grouped with errors** |

## Integration with Existing Build Scripts

The tool works as a drop-in replacement for `make` in your build scripts:

```bash
# Before
cd build && make -j8

# After
./ncut.py -j8
# or
python -m noisecut -j8
```

## Implementation Details

### Automatic Compiler Detection

The parser automatically detects the compiler by analyzing the first compilation line:
- Searches for `gcc`, `g++`, `clang`, `clang++`, `avr-gcc`, etc.
- Switches to the appropriate parser
- Reports detected compiler at the end of build

### Parsed Output Patterns

The build wrapper recognizes these compiler output patterns:

1. **Compilation**: 
   ```
   gcc -c ... -o obj/main.o ../src/main.cpp
   clang++ -c ... -o window.o ../src/window.cpp
   avr-gcc -c ... -o sensor.o sensor.c
   ```

2. **MOC Generation**:
   ```
   /opt/homebrew/share/qt/libexec/moc ... -o moc/moc_window.cpp ../src/window.h
   ```

3. **Warnings/Errors**:
   ```
   ../src/file.cpp:123:45: warning: unused parameter 'foo' [-Wunused-parameter]
   ../src/file.cpp:456:78: error: no matching function
   ```
4. **Additional Context**:
   ```
   ../src/file.h:23:18: note: overridden virtual function is here
   ```

### Issue Grouping Algorithm

Issues are grouped by:
- Type (warning or error)
- Normalized message (variable names stripped)
- Warning category (e.g., `-Wunused-parameter`)

This allows the tool to show:
- "unused parameter" appears in 15 different places (with variable names in parentheses)
- Complete list of all affected files

## Testing

The project includes a comprehensive test suite with **30 unit tests** covering:
- GCC, Clang, AVR-GCC parser functionality
- Severity classification (5 levels, 50+ warning types)
- Smart warning grouping by category
- Deduplication of header warnings
- Large firmware build scenarios (72 warnings, multiple files)
- Make-style output parsing
- Linker error detection

See [tests/README.md](tests/README.md) for details.
The project includes a comprehensive test suite with 16 unit tests. See [tests/README.md](tests/README.md) for details.

### Run Tests

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install test dependencies
pip install -r requirements-dev.txtSee [tests/README.md](tests/README.md) for details.

### Run Tests

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
```

All tests pass with the modular architecture.

## Requirements

- Python 3.7+
- No additional packages required (uses only stdlib)
- Works with GCC, Clang, AVR-GCC, and other compatible compilers

## Pro Tips

1. **Use `-v` when debugging build issues** - shows full compiler commands
2. **Use `--max-locations 20`** to see more warning locations for comprehensive fixes
3. **Pipe to file** if you need to save the output:
   ```bash
   ./ncut.py 2>&1 | tee build.log
   ```

## License

See LICENSE file for details.

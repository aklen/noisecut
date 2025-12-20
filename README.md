# noisecut

Cut through compiler noise. See what really matters.

A modular build output analyzer for C/C++ projects that transforms raw compiler output into clear, actionable insight.

**Keywords:** C++, C, build tools, compiler diagnostics, clang, gcc, build log analysis, warning aggregation, developer tooling, CI, command-line tools

## Overview

`noisecut` is a Python-based build analysis tool that parses GCC/Clang/AVR-GCC compiler output and provides:

- **Automatic compiler detection** - recognizes GCC, Clang, AVR-GCC automatically
- **Colorized output** with ANSI codes for better readability
- **Error/warning grouping** - groups identical issues across files
- **Build statistics** - tracks files compiled, warnings, errors, and duration
- **Modular architecture** - easily extensible with new parsers
- **Clean summary** - hides verbose compiler flags, shows only essentials

noisecut is not a linter or static analyzer — it works purely on compiler output and build logs.

## Features

### Automatic Compiler Detection

Automatically detects the compiler being used and applies the appropriate parser:
- GCC/G++
- Clang/Clang++
- AVR-GCC (for embedded systems)

No need to manually specify the compiler type!

### Intelligent Output Parsing

Parses compiler output and identifies:
- Compilation actions (`[CC]`)
- MOC generation (`[MOC]`) for Qt projects
- Warnings and errors with file locations
- Additional context (notes, overridden functions, etc.)

### Issue Grouping

Groups identical warnings/errors together, showing:
- The warning/error message
- Category (e.g., `-Wunused-parameter`, `-Winconsistent-missing-override`)
- All file locations where it occurs
- Count of occurrences

### Color Coding

- **Cyan**: Compilation and build info
- **Magenta**: MOC (Meta-Object Compiler) generation
- **Yellow**: Warnings
- **Red**: Errors
- **Green**: Success status
- **Bold**: Important messages

Colors are disabled automatically when:
- Output is redirected to a file
- Running in non-interactive mode
- `NO_COLOR` environment variable is set

## Installation

No installation required. Simply ensure you have Python 3.7+ installed:

```bash
python3 --version
```

The package uses only standard library modules.

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
            [--parser {auto,gcc,clang,avr-gcc}] [target]

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
| Group similar warnings | No | Yes |
| Colorized output | No | Yes |
| Build statistics | No | Yes |
| Error summary | Scattered | Grouped at end |
| Show all locations | Need to scroll | Listed together |
| Compiler detection | Manual | Automatic |
| Multiple compilers | Single project | Mixed projects supported |

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
- Message text
- Warning category (e.g., `-Wunused-parameter`)

This allows the tool to show:
- "This unused parameter warning appears in 15 different places"
- Complete list of all affected files

## Requirements

- Python 3.7+
- No additional packages required (uses only stdlib)
- Works with GCC, Clang, AVR-GCC, and other compatible compilers

## Testing

The project includes a comprehensive test suite with 16 unit tests. See [tests/README.md](tests/README.md) for details.

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

## Pro Tips

1. **Use `-v` when debugging build issues** - shows full compiler commands
2. **Use `--max-locations 20`** to see more warning locations for comprehensive fixes
3. **Pipe to file** if you need to save the output:
   ```bash
   ./ncut.py 2>&1 | tee build.log
   ```

## License

See LICENSE file for details.

# noisecut

Cut through compiler noise. See what really matters.

A build output analyzer for C/C++ projects that transforms raw compiler output into clear, actionable insight.

## Overview

`noisecut` is a Python-based build wrapper that parses GCC/Clang compiler output and provides:

- **Colorized output** with ANSI codes for better readability
- **Error/warning grouping** - groups identical issues across files
- **Build statistics** - tracks files compiled, warnings, errors, and duration
- **Clean summary** - hides verbose compiler flags, shows only essentials

## Features

### Intelligent Output Parsing

Parses GCC/Clang compiler output and identifies:
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

The script uses only standard library modules.

## Usage

### Parse Build Output from File

Parse compiler output that was saved to a file:

```bash
./ncut.py -f build_output.txt
```

This is useful for:
- Analyzing builds from CI/CD pipelines
- Reviewing historical build logs
- Testing and debugging the parser
- Sharing build analysis with team members

### Run Live Build

```bash
./ncut.py
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

## Command Line Options

```
usage: ncut.py [-h] [-v] [-f FILE] [-j JOBS] [--clean] [--max-locations MAX_LOCATIONS] [target]

Build output analyzer with enhanced error reporting

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
```

## Comparison with Standard Make Output

| Feature | `make -j8` | `ncut.py` |
|---------|-----------|-----------|
| See compilation progress | Verbose flags | Clean summary |
| Group similar warnings | No | Yes |
| Colorized output | No | Yes |
| Build statistics | No | Yes |
| Error summary | Scattered | Grouped at end |
| Show all locations | Need to scroll | Listed together |

## Integration with Existing Build Scripts

The tool works as a drop-in replacement for `make` in your build scripts:

```bash
# Before
cd build && make -j8

# After
./ncut.py -j8
```

## Implementation Details

### Parsed Output Patterns

The build wrapper recognizes these compiler output patterns:

1. **Compilation**: 
   ```
   /usr/bin/clang++ ... -o obj/main.o ../src/main.cpp
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

The project includes a comprehensive test suite. See [tests/README.md](tests/README.md) for details.

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
- Works with GCC and Clang compilers

## Pro Tips

1. **Use `-v` when debugging build issues** - shows full compiler commands
2. **Use `--max-locations 20`** to see more warning locations for comprehensive fixes
3. **Pipe to file** if you need to save the output:
   ```bash
   ./ncut.py 2>&1 | tee build.log
   ```

## License

See LICENSE file for details.

# noisecut

Cut through compiler noise. See what really matters.

A Python build output analyzer for C/C++/.NET/Rust that groups warnings by severity and category, making critical issues immediately visible.

## Features

- **Smart Grouping** - Groups warnings by category (e.g., all "unused parameter" warnings together)
- **Severity Classification** - 5-level system (INFO→LOW→MEDIUM→HIGH→CRITICAL) with 100+ warning types
- **Visual Priority** - Critical warnings at bottom in red, no scrolling needed
- **Auto-Detection** - Recognizes GCC, Clang, AVR-GCC, .NET/MSBuild, Rust automatically
- **Extensible** - Add new compilers in ~3 lines via registry system
- **Parse Anywhere** - Works with live builds, saved logs, CI/CD output
- **Zero Dependencies** - Pure Python 3.7+ stdlib

## Installation

```bash
# Recommended: pipx (isolated environment)
pipx install git+https://github.com/aklen/noisecut.git

# Alternative: pip
pip install --user git+https://github.com/aklen/noisecut.git
```

## Quick Start

```bash
# Parse saved build log
ncut -f build_output.txt

# Live build (C/C++)
make 2>&1 | ncut

# Live build (Rust)
cargo build 2>&1 | ncut
cargo test 2>&1 | ncut

# With options
ncut -f build.log --max-locations 20 --no-severity

# Filter by severity
make 2>&1 | ncut --errors-only          # Only errors
cargo build 2>&1 | ncut --min-level high  # HIGH+ warnings and errors
```

## Example Output

```
⚠ WARNING [INFO]: #warning "Debug mode"
⚠ WARNING [MEDIUM]: unused parameter (5 occurrences)
  └─ src/main.c:45 (argc), src/util.c:89 (flags), ...
⚠ WARNING [HIGH]: implicit-fallthrough (63 occurrences)
  └─ driver/comm.c:457, :458, :459, ...
⚠ WARNING [CRITICAL]: control reaches end of non-void function
  └─ src/parser.c:234
✗ ERROR: undefined reference to 'engine_update'
  └─ modules/control.c:211
```

## How It Works

### Smart Grouping
- `unused parameter 'flags'` + `unused parameter 'argc'` → **"unused parameter" (2×)**
- Shows variable names in parentheses: `(flags), (argc)`
- Groups by category + normalized message

### Severity Sorting
Issues sorted least→most important, **critical at bottom**:
1. **INFO/LOW** (cyan) - #warning directives, style issues
2. **MEDIUM** (white) - unused vars, shadowing
3. **HIGH** (red) - sign-compare, overflow, implicit-fallthrough
4. **CRITICAL** (red bold) - dangling pointers, return-type, UB
5. **ERRORS** (red bold) - build failures

## Command Options

```bash
ncut [options] [target]

  -f FILE              Parse from file or stdin pipe
  -v, --verbose        Show full compiler output
  -j JOBS              Parallel jobs (default: 8)
  --clean              Clean before building
  --max-locations N    Show N locations per issue (default: 5)
  --no-severity        Disable severity badges
  --errors-only        Show only errors, suppress warnings
  --min-level LEVEL    Minimum severity: info/low/medium/high/critical/error
  --parser TYPE        Force parser: gcc, clang, avr-gcc, dotnet, rust (default: auto)
```

## Comparison vs Standard Make

| Feature | make | ncut |
|---------|------|------|
| Group by category | ❌ | ✅ |
| Severity classification | ❌ | ✅ 5 levels |
| Critical at bottom | ❌ | ✅ |
| Color badges | ❌ | ✅ |
| Auto-detect compiler | ❌ | ✅ |
| Parse make/bullet format | ❌ | ✅ |
| Severity filtering | ❌ | ✅ |
| Stdin/pipe support | ✅ | ✅ |

## Testing

30 comprehensive tests covering parsers, grouping, severity, deduplication.

```bash
pytest tests/ -v  # All 30 tests pass
```

## License

MIT - See LICENSE file

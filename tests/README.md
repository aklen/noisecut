# Test Suite for noisecut

This directory contains the test suite for the noisecut build output analyzer.

## Structure

```
tests/
├── test_ncut.py          # Main unit tests
├── samples/              # Sample compiler outputs for testing
│   ├── gcc_warnings.txt
│   ├── clang_errors.txt
│   ├── avr_gcc_build.txt
│   ├── qt_moc_build.txt
│   └── gcc_multiple_errors.txt
└── README.md             # This file
```

## Running Tests

### Prerequisites

Install pytest:

```bash
pip install pytest
```

### Run All Tests

```bash
# From project root
pytest tests/

# Or with verbose output
pytest tests/ -v
```

### Run Specific Test Class

```bash
pytest tests/test_ncut.py::TestBuildOutputParser -v
```

### Run Specific Test

```bash
pytest tests/test_ncut.py::TestBuildOutputParser::test_parse_warning -v
```

## Test Coverage

The test suite covers:

### Parser Tests (`TestBuildOutputParser`)
- GCC compilation line parsing
- Clang compilation line parsing
- Qt MOC generation parsing
- Warning detection and parsing
- Error detection and parsing
- Note/context parsing
- Multiple warnings in sequence

### Grouping Tests (`TestIssueGrouping`)
- Grouping identical warnings from different files
- Preserving all file locations
- Sorting by occurrence count

### File Input Tests (`TestFileInput`)
- Parsing GCC warning output from file
- Parsing Clang error output from file
- Parsing AVR-GCC build output from file
- Parsing Qt MOC build output from file
- Parsing multiple errors from file

### Data Structure Tests (`TestBuildIssue`)
- Issue equality for grouping
- Issue inequality for different messages
- Hash consistency

## Sample Files

The `samples/` directory contains real-world compiler output examples:

- **gcc_warnings.txt**: GCC compiler warnings (unused parameters, variables, sign comparison)
- **clang_errors.txt**: Clang errors and warnings (missing override, type mismatch)
- **avr_gcc_build.txt**: AVR-GCC embedded build output with memory usage
- **qt_moc_build.txt**: Qt MOC generation with override warnings
- **gcc_multiple_errors.txt**: Multiple compilation errors in one build

These files are used for integration testing to ensure the parser handles various compiler outputs correctly.

## Testing the File Input Feature

You can manually test the file input feature:

```bash
# Parse a sample file
./ncut.py -f tests/samples/gcc_warnings.txt

# Parse with verbose output
./ncut.py -f tests/samples/clang_errors.txt -v

# Show more locations per issue
./ncut.py -f tests/samples/avr_gcc_build.txt --max-locations 10
```

## Adding New Tests

When adding new test cases:

1. Add sample compiler output to `samples/` directory
2. Write corresponding test in `test_ncut.py`
3. Run tests to ensure they pass
4. Update this README if needed

## Continuous Integration

These tests are designed to run in CI environments. They:
- Use no external dependencies except pytest
- Don't require network access
- Don't require actual compilers installed
- Run quickly (< 1 second)

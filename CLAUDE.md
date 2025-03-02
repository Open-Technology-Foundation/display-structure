## Command Reference
- Run script: 
  - Multiple tables: `./display-structure <database> <table1> <table2> <table3>`
  - Format options: `./display-structure <db> <table> -f json|csv`
  - Column filtering: `./display-structure <db> <table> -c Field,Type,Null`
  - Table statistics: `./display-structure <db> <table> -s`
  - Disable color: `./display-structure <db> <table> -n`
  - Bypass cache: `./display-structure <db> <table> -N`
  - Save output: `./display-structure <db> <table> -f csv -o output.csv`
  - Show version: `./display-structure -v`
  - Pipe mode: `mysql <db> -e 'show columns from <table>' | ./display-structure`
- Testing: 
  - `./display-structure peraturan peraturan_distinct -s` (test formatting and stats)
  - `./display-structure peraturan peraturan_distinct -f json` (test JSON output)
  - `cat test_data.txt | ./display-structure` (test with sample data file)
- Linting: `flake8 display-structure.py`

## Code Style
- Python: 
  - 2-space indentation, shebang line `#!/usr/bin/env python3`
  - Module docstring with author, license, and version information
  - Import order: standard lib (sys, re, os, etc.), third-party, local modules
  - Constants: Define at top of files, use UPPER_CASE
  - Use descriptive function and variable names (e.g., `parse_mysql_table`)
  - Docstrings for all functions; comment complex logic sections
  - Error handling: Use try/except with specific error messages
  - Color output: Use ANSI color constants defined in Colors class
  - End files with '#fin' marker

- Shell scripts:
  - Shebang: `#!/bin/bash`  
  - Always `set -euo pipefail` at start for error handling
  - 2-space indentation
  - Declare variables before use with `declare` statements
  - Prefer `[[` over `[` for conditionals
  - Always end scripts with '\n#fin\n' to indicate the end of script

## Project Conventions
- This utility formats MySQL table structure with enhanced features:
  - Version 1.0.0 (GPL-3.0 license)
  - Supports multiple tables in a single command
  - Multiple output formats (table, JSON, CSV) with file export
  - Column filtering and colorized output (primary keys, data types)
  - Automatic caching of results (1-hour cache in ~/.cache/mysql-display-structure)
  - Table statistics with row count, size, and index information
  - Short command-line options for all flags
  - Adaptive column width based on terminal size

## Environment
- Python 3.6+ (developed on Python 3.12)
- MySQL 8.0
- Dependencies: standard library only (no external packages)
- Testing environment: Ubuntu 24.04 LTS


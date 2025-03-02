
# MySQL Display Structure Tool

A utility to format and display MySQL table structure with proper column alignment, enum handling, color highlighting, and multiple output formats.

![GPL-3.0 License](https://img.shields.io/badge/License-GPL_3.0-blue.svg)
![Version](https://img.shields.io/badge/Version-1.0.0-green.svg)

## Features

- **Multiple Table Support**: Process several tables in one command
- **Output Formats**: Table (default), JSON, and CSV formats with file export
- **Column Filtering**: Display only the columns you need
- **Color Highlighting**: Visual distinction for keys, data types, and constraints
- **Table Statistics**: View row count, size, and index information
- **Result Caching**: Automatic one-hour cache for better performance
- **Smart Enum Handling**: Clean formatting with intelligent line wrapping
- **Terminal Adaptation**: Automatically adjusts to your terminal width

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/garydean/mysql-display-structure.git
   cd mysql-display-structure
   ```

2. Make the script executable:
   ```
   chmod +x display-structure
   ```

3. Optional: Add to your PATH (for system-wide access):
   ```
   sudo ln -s $(pwd)/display-structure /usr/local/bin/
   ```

## Usage Examples

### Basic Usage

```
display-structure <database> <table>
```

### Display Multiple Tables

```
display-structure peraturan peraturan_distinct peraturan_tahun
```

### Filter Specific Columns

```
display-structure peraturan peraturan_distinct -c Field,Type,Null
```

### Show Table Statistics

```
display-structure peraturan peraturan_distinct -s
```

### Export to JSON or CSV

```
display-structure peraturan peraturan_distinct -f json
display-structure peraturan peraturan_distinct -f csv -o structure.csv
```

### Pipe from MySQL

```
mysql peraturan -e 'show columns from peraturan_distinct' | ./display-structure
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--columns` | `-c` | Comma-separated list of columns to display |
| `--format` | `-f` | Output format: table (default), json, csv |
| `--stats` | `-s` | Show table statistics (row count, size, etc.) |
| `--output` | `-o` | Write output to file (for json/csv formats) |
| `--no-color` | `-n` | Disable colorized output |
| `--no-cache` | `-N` | Bypass cache and force fresh data |
| `--version` | `-V` | Show version information |
| `--help` | `-h` | Show this help message |

## Data Caching

The tool automatically caches query results for one hour in `~/.cache/mysql-display-structure/`. 
Use the `-N` flag to bypass the cache and get fresh data.

## Requirements

- Python 3.6+
- MySQL client

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) - see the LICENSE file for details.

## Authors

- Gary Dean with Claude Code 0.2.29


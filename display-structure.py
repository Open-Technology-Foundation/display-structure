#!/usr/bin/env python3
"""
MySQL Display Structure Tool

A utility to format and display MySQL table structure with proper column alignment, 
enum handling, colorized output, and multiple export formats.

Author: Gary Dean with Claude Code 0.2.29
License: GPL-3.0
Version: 1.0.0
"""

import sys
import re
import os
import json
import csv
import shutil
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime

# Version information
VERSION = "1.0.0"
AUTHOR = "Gary Dean with Claude Code 0.2.29"
LICENSE = "GPL-3.0"


# ANSI color codes for colorized output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


# Cache directory and maximum cache age (1 hour)
CACHE_DIR = Path.home() / ".cache" / "mysql-display-structure"
CACHE_MAX_AGE = 3600  # seconds


def get_terminal_width():
    """Get the width of the terminal"""
    return shutil.get_terminal_size().columns


def get_cache_key(database, table, columns=None, format_type="table"):
    """Generate a unique cache key based on query parameters"""
    column_str = "_".join(columns) if columns else "all"
    return f"{database}_{table}_{column_str}_{format_type}"


def get_from_cache(cache_key):
    """Try to get result from cache"""
    cache_file = CACHE_DIR / f"{cache_key}.cache"
    
    # Check if cache exists and is not too old
    if cache_file.exists():
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age < CACHE_MAX_AGE:
            try:
                with open(cache_file, 'r') as f:
                    return json.loads(f.read())
            except Exception:
                # If any error occurs, ignore cache
                pass
    
    return None


def save_to_cache(cache_key, data):
    """Save result to cache"""
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to cache file
    cache_file = CACHE_DIR / f"{cache_key}.cache"
    try:
        with open(cache_file, 'w') as f:
            f.write(json.dumps(data))
    except Exception:
        # If cache saving fails, just ignore it
        pass


def run_mysql_command(database, table, stats=False):
    """Run a MySQL command to get table structure and return the output"""
    try:
        # Get table structure
        cmd = ["mysql", database, "-e", f"SHOW COLUMNS FROM {table}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        
        # If stats requested, get additional table statistics
        if stats:
            stats_data = {}
            
            # Get row count
            try:
                cmd = ["mysql", database, "-e", f"SELECT COUNT(*) FROM {table}"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                rows = result.stdout.strip().splitlines()
                if len(rows) > 1:
                    stats_data['row_count'] = rows[1].strip()
            except Exception:
                stats_data['row_count'] = "Error"
            
            # Get table size
            try:
                cmd = ["mysql", database, "-e", 
                       f"SELECT table_schema, table_name, "
                       f"round(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)' "
                       f"FROM information_schema.TABLES "
                       f"WHERE table_schema = '{database}' AND table_name = '{table}'"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                rows = result.stdout.strip().splitlines()
                if len(rows) > 1:
                    size_parts = rows[1].strip().split('\t')
                    if len(size_parts) > 2:
                        stats_data['size_mb'] = size_parts[2]
            except Exception:
                stats_data['size_mb'] = "Error"
            
            # Get index information
            try:
                cmd = ["mysql", database, "-e", f"SHOW INDEX FROM {table}"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                rows = result.stdout.strip().splitlines()
                if len(rows) > 1:
                    stats_data['index_count'] = str(len(rows) - 1)
            except Exception:
                stats_data['index_count'] = "Error"
            
            return lines, stats_data
        
        return lines, {}
    
    except subprocess.CalledProcessError as e:
        print(f"Error executing MySQL command: {e}", file=sys.stderr)
        print(f"MySQL Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: MySQL client not found. Please ensure MySQL is installed.", file=sys.stderr)
        sys.exit(1)


def parse_mysql_table(lines, filter_columns=None):
    """Parse the MySQL table output into a structured format"""
    if not lines:
        return [], [], []
    
    # Extract headers and data
    headers = []
    data = []
    column_widths = []
    
    # Check if we have tab-delimited output
    if '\t' in lines[0]:
        # Tab-delimited format
        headers = lines[0].split('\t')
        for i in range(1, len(lines)):
            if not lines[i].strip():
                continue
            data.append(lines[i].split('\t'))
    else:
        # Find header line in pipe-delimited format
        header_line = None
        for i, line in enumerate(lines):
            if line.startswith('| Field'):
                header_line = i
                break
        
        if header_line is None:
            return [], [], []
        
        # Extract headers
        headers = [h.strip() for h in lines[header_line].split('|')[1:-1]]
        
        # Extract data rows
        for i in range(header_line + 2, len(lines)):
            if lines[i].startswith('+--'):
                continue
            if not lines[i].strip():
                continue
            
            row = [cell.strip() for cell in lines[i].split('|')[1:-1]]
            data.append(row)
    
    # Filter columns if specified
    if filter_columns:
        # Find indices of requested columns
        selected_indices = []
        selected_headers = []
        
        for i, header in enumerate(headers):
            if header in filter_columns:
                selected_indices.append(i)
                selected_headers.append(header)
        
        # Filter data rows
        filtered_data = []
        for row in data:
            filtered_row = [row[i] for i in selected_indices if i < len(row)]
            filtered_data.append(filtered_row)
        
        headers = selected_headers
        data = filtered_data
    
    # Calculate initial column widths
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in data:
            if i < len(row):
                # For enum fields, we'll handle them specially
                if 'enum(' in row[i]:
                    # Find the longest enum value
                    enum_values = re.findall(r"'[^']*'", row[i])
                    longest_enum = max([len(val) for val in enum_values], default=0)
                    # Add some padding for 'enum(' and ')'
                    enum_prefix_len = len("enum(")
                    # Reduced padding from +2 to +1
                    max_width = max(max_width, longest_enum + enum_prefix_len + 1)
                else:
                    max_width = max(max_width, len(row[i]))
        column_widths.append(max_width)
    
    return headers, data, column_widths


def get_enum_values(enum_str):
    """Extract enum values from an enum string"""
    match = re.search(r'enum\((.*)\)', enum_str)
    if not match:
        return []
    
    enum_content = match.group(1)
    return re.findall(r"'[^']*'", enum_content)


def format_enum(enum_str, column_width):
    """Format an enum string to wrap at appropriate places"""
    enum_values = get_enum_values(enum_str)
    if not enum_values:
        return [enum_str]
    
    # Start building the output
    lines = []
    first_line = "enum("
    
    # Add first value to first line
    if enum_values:
        first_line += enum_values[0]
        if len(enum_values) > 1:
            first_line += ","
    
    lines.append(first_line)
    
    # Add remaining values with minimal formatting
    current_line = ""
    for i in range(1, len(enum_values)):
        val = enum_values[i]
        # Add comma if not the last item
        if i < len(enum_values) - 1:
            val += ","
        
        # Reduced padding: Use exact width check instead of -2
        if not current_line:
            current_line = val
        elif len(current_line + " " + val) > column_width:
            lines.append(current_line)
            current_line = val
        else:
            current_line += " " + val
    
    # Add the last line if not empty
    if current_line:
        lines.append(current_line)
    
    # Add closing parenthesis to the last line
    if lines:
        if lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1] + ")"
        else:
            lines[-1] += ")"
    
    return lines


def colorize_cell(cell, header, colorize=True):
    """Apply appropriate color to a cell based on content"""
    if not colorize:
        return cell
    
    # Colorize based on column type
    if header.lower() == 'key':
        if cell == 'PRI':
            return f"{Colors.BOLD}{Colors.RED}{cell}{Colors.RESET}"
        elif cell == 'UNI':
            return f"{Colors.BOLD}{Colors.BLUE}{cell}{Colors.RESET}"
        elif cell == 'MUL':
            return f"{Colors.BOLD}{Colors.GREEN}{cell}{Colors.RESET}"
    elif header.lower() == 'null':
        if cell == 'NO':
            return f"{Colors.BOLD}{Colors.RED}{cell}{Colors.RESET}"
        elif cell == 'YES':
            return f"{Colors.GREEN}{cell}{Colors.RESET}"
    elif header.lower() == 'type':
        # Highlight data types
        if 'int' in cell.lower():
            return f"{Colors.CYAN}{cell}{Colors.RESET}"
        elif 'char' in cell.lower() or 'text' in cell.lower():
            return f"{Colors.GREEN}{cell}{Colors.RESET}"
        elif 'date' in cell.lower() or 'time' in cell.lower():
            return f"{Colors.YELLOW}{cell}{Colors.RESET}"
        elif 'enum' in cell.lower():
            return f"{Colors.MAGENTA}{cell}{Colors.RESET}"
    elif header.lower() == 'extra':
        if 'auto_increment' in cell.lower():
            return f"{Colors.BOLD}{Colors.YELLOW}{cell}{Colors.RESET}"
    
    return cell


def print_formatted_table(headers, data, column_widths, stats=None, colorize=True):
    """Print the table with formatted enum values"""
    term_width = get_terminal_width()
    
    # Find the Type column index
    type_col_index = -1
    for i, header in enumerate(headers):
        if header.lower() == 'type':
            type_col_index = i
            break
    
    if type_col_index == -1 and len(headers) > 1:
        type_col_index = 1  # Assume second column is Type
    
    # Calculate available width for type column if it exists
    if type_col_index != -1:
        # Calculate total width of non-Type columns
        non_type_width = sum(column_widths) - column_widths[type_col_index]
        # Add padding and separators
        non_type_width += (len(column_widths) - 1) * 3 + 4  # 3 chars per column (space+pipe+space) + 4 for outer pipes
        
        # Calculate available width for Type column
        available_width = term_width - non_type_width
        # Ensure reasonable minimum width
        type_width = max(column_widths[type_col_index], min(available_width, 50))
        column_widths[type_col_index] = type_width
    
    # Print table statistics if available
    if stats:
        if colorize:
            print(f"{Colors.BOLD}Table Statistics:{Colors.RESET}")
            print(f"• Row Count: {Colors.CYAN}{stats.get('row_count', 'N/A')}{Colors.RESET}")
            print(f"• Size: {Colors.CYAN}{stats.get('size_mb', 'N/A')} MB{Colors.RESET}")
            print(f"• Index Count: {Colors.CYAN}{stats.get('index_count', 'N/A')}{Colors.RESET}")
        else:
            print("Table Statistics:")
            print(f"• Row Count: {stats.get('row_count', 'N/A')}")
            print(f"• Size: {stats.get('size_mb', 'N/A')} MB")
            print(f"• Index Count: {stats.get('index_count', 'N/A')}")
        print()
    
    # Print header separator
    separator = "+"
    for width in column_widths:
        separator += "-" * (width + 2) + "+"
    print(separator)
    
    # Print headers
    header_line = "|"
    for i, header in enumerate(headers):
        if colorize:
            header_display = f"{Colors.BOLD}{header}{Colors.RESET}"
        else:
            header_display = header
        
        # Account for ANSI color codes in width calculation
        visible_len = len(header)
        header_line += f" {header_display.ljust(visible_len)} " + " " * (column_widths[i] - visible_len) + "|"
    
    print(header_line)
    
    # Print header/data separator
    print(separator)
    
    # Print data rows
    for row in data:
        # Ensure row has enough elements
        while len(row) < len(headers):
            row.append("")
        
        # Check if this row has an enum that needs special handling
        has_enum = False
        enum_col = -1
        enum_lines = []
        
        if type_col_index != -1 and type_col_index < len(row):
            if 'enum(' in row[type_col_index] and len(row[type_col_index]) > 40:
                has_enum = True
                enum_col = type_col_index
                enum_lines = format_enum(row[type_col_index], column_widths[type_col_index])
        
        if not has_enum:
            # Print normal row
            row_line = "|"
            for i, cell in enumerate(row):
                if i < len(column_widths):  # Ensure we don't go out of bounds
                    colored_cell = colorize_cell(cell, headers[i], colorize)
                    # Account for ANSI color codes in width calculation
                    visible_len = len(cell)
                    row_line += f" {colored_cell.ljust(visible_len)} " + " " * (column_widths[i] - visible_len) + "|"
            print(row_line)
        else:
            # Print row with wrapped enum
            for j, enum_line in enumerate(enum_lines):
                row_line = "|"
                for i, cell in enumerate(row):
                    if i < len(column_widths):  # Ensure we don't go out of bounds
                        if i == enum_col:
                            # No space padding after enum content - exact fit for last line
                            if j == len(enum_lines) - 1:
                                if colorize:
                                    colored_enum = f"{Colors.MAGENTA}{enum_line}{Colors.RESET}"
                                else:
                                    colored_enum = enum_line
                                    
                                # Ensure we properly format the closing parenthesis in enum
                                # Calculate how much space we need to align everything
                                filler_space = column_widths[i] - len(enum_line)
                                row_line += f" {colored_enum}" + " " * filler_space + " |"
                            else:
                                if colorize:
                                    colored_enum = f"{Colors.MAGENTA}{enum_line}{Colors.RESET}"
                                else:
                                    colored_enum = enum_line
                                    
                                # Account for ANSI color codes in width calculation
                                visible_len = len(enum_line)
                                row_line += f" {colored_enum.ljust(visible_len)} " + " " * (column_widths[i] - visible_len) + "|"
                        else:
                            if j == 0:
                                colored_cell = colorize_cell(cell, headers[i], colorize)
                                # Account for ANSI color codes in width calculation
                                visible_len = len(cell)
                                row_line += f" {colored_cell.ljust(visible_len)} " + " " * (column_widths[i] - visible_len) + "|"
                            else:
                                row_line += " " + " ".ljust(column_widths[i]) + " |"
                print(row_line)
    
    # Print footer separator
    print(separator)


def export_json(headers, data, output_file=None):
    """Export table data as JSON"""
    result = []
    for row in data:
        row_dict = {}
        for i, header in enumerate(headers):
            if i < len(row):
                row_dict[header] = row[i]
            else:
                row_dict[header] = ""
        result.append(row_dict)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"JSON data exported to {output_file}")
    else:
        print(json.dumps(result, indent=2))


def export_csv(headers, data, output_file=None):
    """Export table data as CSV"""
    if output_file:
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
        print(f"CSV data exported to {output_file}")
    else:
        writer = csv.writer(sys.stdout)
        writer.writerow(headers)
        writer.writerows(data)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Display MySQL table structure with formatted output')
    parser.add_argument('database', nargs='?', help='Database name')
    parser.add_argument('table', nargs='*', help='Table name(s)')
    parser.add_argument('--columns', '-c', help='Comma-separated list of columns to display')
    parser.add_argument('--format', '-f', choices=['table', 'json', 'csv'], 
                      default='table', help='Output format (default: table)')
    parser.add_argument('--stats', '-s', action='store_true', 
                      help='Show table statistics (row count, size, etc.)')
    parser.add_argument('--no-color', '-n', action='store_true', help='Disable colorized output')
    parser.add_argument('--no-cache', '-N', action='store_true', help='Bypass cache and force fresh data')
    parser.add_argument('--output', '-o', help='Write output to file (for json/csv formats)')
    parser.add_argument('--version', '-V', action='store_true', help='Show version information')
    return parser.parse_args()


def show_version():
    """Display version information"""
    print(f"MySQL Display Structure Tool v{VERSION}")
    print(f"Author: {AUTHOR}")
    print(f"License: {LICENSE}")
    print("\nA utility to format and display MySQL table structure with enhanced features.")


def main():
    args = parse_arguments()
    
    # Check if version flag is provided
    if args.version:
        show_version()
        return
    
    # Process column filter if provided
    filter_columns = None
    if args.columns:
        filter_columns = [col.strip() for col in args.columns.split(',')]
    
    # Determine if we should use colorized output (default: true)
    colorize = not args.no_color
    
    # Handle input from either arguments or stdin
    if args.database:
        if not args.table:
            print("Error: Please provide at least one table name", file=sys.stderr)
            sys.exit(1)
        
        # Process each table
        for i, table in enumerate(args.table):
            # Add a separator between tables
            if i > 0:
                print("\n" + "=" * 80 + "\n")
            
            if colorize:
                print(f"{Colors.BOLD}Database:{Colors.RESET} {args.database}, {Colors.BOLD}Table:{Colors.RESET} {table}")
            else:
                print(f"Database: {args.database}, Table: {table}")
            
            # Try to get from cache if caching is enabled
            cache_key = None
            cached_data = None
            
            if not args.no_cache:
                cache_key = get_cache_key(args.database, table, filter_columns, args.format)
                cached_data = get_from_cache(cache_key)
            
            if cached_data:
                headers = cached_data['headers']
                data = cached_data['data']
                column_widths = cached_data['column_widths']
                stats = cached_data.get('stats', {})
            else:
                # Get fresh data
                lines, stats = run_mysql_command(args.database, table, args.stats)
                headers, data, column_widths = parse_mysql_table(lines, filter_columns)
                
                # Cache the data if caching is enabled
                if cache_key:
                    save_to_cache(cache_key, {
                        'headers': headers,
                        'data': data, 
                        'column_widths': column_widths,
                        'stats': stats
                    })
            
            # Handle export format
            if args.format == 'json':
                export_json(headers, data, args.output)
            elif args.format == 'csv':
                export_csv(headers, data, args.output)
            else:  # table format
                print_formatted_table(headers, data, column_widths, stats if args.stats else None, colorize)
    else:
        # Read from stdin
        lines = [line.rstrip() for line in sys.stdin]
        headers, data, column_widths = parse_mysql_table(lines, filter_columns)
        
        if not headers or not data:
            print("Error: Could not parse MySQL table structure", file=sys.stderr)
            return
        
        # Handle export format
        if args.format == 'json':
            export_json(headers, data, args.output)
        elif args.format == 'csv':
            export_csv(headers, data, args.output)
        else:  # table format
            print_formatted_table(headers, data, column_widths, None, colorize)


if __name__ == "__main__":
    main()

#fin
    
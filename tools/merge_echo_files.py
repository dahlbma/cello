#!/usr/bin/env python3
"""
Merge Echo dispenser output files into import format.

This script processes Echo instrument output files (initial spotting and repair)
and combines them into a single import file suitable for uploading to Cello.

Usage:
    python tools/merge_echo_files.py ECHO.csv ECHO_REPAIR.csv -o echo_import.csv
    python tools/merge_echo_files.py ECHO.csv -o echo_import.csv  # Single file only
"""

import csv
import argparse
import sys
from pathlib import Path


def read_echo_details(file_path):
    """
    Read Echo CSV file and extract data from [DETAILS] section.
    
    For ECHO.csv (initial spotting):
        - Skip lines until [EXCEPTIONS]
        - Continue skipping until [DETAILS]
        - Read data after [DETAILS]
    
    For ECHO_REPAIR.csv (repair spotting):
        - Skip lines until [DETAILS]
        - Read data after [DETAILS]
    
    Args:
        file_path: Path to Echo CSV file
        
    Returns:
        List of dictionaries containing the detail rows
    """
    details_data = []
    in_details_section = False
    found_exceptions = False
    headers = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Track if we've seen [EXCEPTIONS] section
            if '[EXCEPTIONS]' in line:
                found_exceptions = True
                continue
            
            # Look for [DETAILS] section
            if '[DETAILS]' in line:
                in_details_section = True
                continue
            
            # If we're in the details section, process the data
            if in_details_section:
                if not line or line.startswith('['):
                    # End of details section or new section starting
                    break
                
                # First non-empty line after [DETAILS] is the header
                if headers is None:
                    headers = [h.strip() for h in line.split(',')]
                    continue
                
                # Parse data rows
                # Handle potential commas within quoted fields
                reader = csv.DictReader([line], fieldnames=headers)
                try:
                    row = next(reader)
                    details_data.append(row)
                except:
                    # Skip malformed rows
                    continue
    
    return details_data


def normalize_well(well):
    """
    Normalize well name to zero-filled format (A1 -> A01, B2 -> B02).
    
    Args:
        well: Well name string (e.g., 'A1', 'A01', 'P24')
        
    Returns:
        Zero-filled well name (e.g., 'A01', 'A01', 'P24')
    """
    if not well:
        return well
    
    # Extract row letter(s) and column number
    import re
    match = re.match(r'^([A-Za-z]+)(\d+)$', well)
    if match:
        row = match.group(1).upper()
        col = int(match.group(2))
        return f"{row}{col:02d}"
    
    return well


def map_echo_to_import(echo_data):
    """
    Map Echo output columns to import file columns.
    
    Column mapping:
        Destination Plate Barcode -> Plate Id
        Destination Well -> Well
        Sample ID -> Compound Id
        Sample Name -> Batch
        Fluid Type -> Form
        Sample Comment -> Conc mM
        Actual Volume -> Volume nL
    
    Args:
        echo_data: List of dictionaries from Echo file
        
    Returns:
        List of dictionaries with mapped columns
    """
    import_data = []
    
    for row in echo_data:
        # Map columns
        well = row.get('Destination Well', '').strip()
        import_row = {
            'Plate Id': row.get('Destination Plate Barcode', '').strip(),
            'Well': normalize_well(well),
            'Compound Id': row.get('Sample ID', '').strip(),
            'Batch': row.get('Sample Name', '').strip(),
            'Form': row.get('Fluid Type', '').strip(),
            'Conc mM': row.get('Sample Comment', '').strip(),
            'Volume nL': row.get('Actual Volume', '').strip()
        }
        
        # Only add rows with essential data
        if import_row['Plate Id'] and import_row['Well']:
            import_data.append(import_row)
    
    return import_data


def merge_echo_files(echo_file, repair_file=None):
    """
    Merge data from Echo initial spotting and repair files.
    
    Args:
        echo_file: Path to initial Echo output file (ECHO.csv)
        repair_file: Optional path to repair Echo output file (ECHO_REPAIR.csv)
        
    Returns:
        List of dictionaries with combined import data
    """
    all_data = []
    
    # Process initial echo file
    if echo_file:
        print(f"Reading initial Echo file: {echo_file}")
        echo_details = read_echo_details(echo_file)
        echo_import = map_echo_to_import(echo_details)
        all_data.extend(echo_import)
        print(f"  Found {len(echo_import)} detail rows")
    
    # Process repair file if provided
    if repair_file:
        print(f"Reading repair Echo file: {repair_file}")
        repair_details = read_echo_details(repair_file)
        repair_import = map_echo_to_import(repair_details)
        all_data.extend(repair_import)
        print(f"  Found {len(repair_import)} detail rows")
    
    return all_data


def write_import_file(data, output_path):
    """
    Write combined data to import CSV file.
    
    Args:
        data: List of dictionaries with import data
        output_path: Path to output CSV file
    """
    if not data:
        print("Warning: No data to write")
        return
    
    columns = ['Plate Id', 'Well', 'Compound Id', 'Batch', 'Form', 'Conc mM', 'Volume nL']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\nWrote {len(data)} rows to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Merge Echo dispenser output files into import format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge initial and repair files
  python tools/merge_echo_files.py ECHO.csv ECHO_REPAIR.csv -o echo_import.csv
  
  # Process only initial file
  python tools/merge_echo_files.py ECHO.csv -o echo_import.csv
  
  # Process only repair file
  python tools/merge_echo_files.py --repair ECHO_REPAIR.csv -o echo_import.csv
        """
    )
    
    parser.add_argument('echo_file', nargs='?', help='Initial Echo output file (ECHO.csv)')
    parser.add_argument('repair_file', nargs='?', help='Repair Echo output file (ECHO_REPAIR.csv)')
    parser.add_argument('-o', '--output', default='echo_import.csv',
                        help='Output import file (default: echo_import.csv)')
    parser.add_argument('--repair', dest='repair_only', 
                        help='Process only a repair file (alternative syntax)')
    
    args = parser.parse_args()
    
    # Handle different argument combinations
    echo_file = args.echo_file
    repair_file = args.repair_file or args.repair_only
    
    # Validate input files
    if not echo_file and not repair_file:
        parser.error("At least one input file is required")
    
    if echo_file and not Path(echo_file).exists():
        print(f"Error: File not found: {echo_file}", file=sys.stderr)
        sys.exit(1)
    
    if repair_file and not Path(repair_file).exists():
        print(f"Error: File not found: {repair_file}", file=sys.stderr)
        sys.exit(1)
    
    # Process files
    try:
        import_data = merge_echo_files(echo_file, repair_file)
        write_import_file(import_data, args.output)
        print("\nSuccess!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

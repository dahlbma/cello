#!/usr/bin/env python3
"""
Verify that SMILES in an Excel file were converted to records in an SDF.

Usage:
  python tools/verify_sdf_conversion.py --input-xlsx input.xlsx --sdf out.sdf --smiles-col smiles

The script counts non-null SMILES in the Excel file and SDF records. If RDKit is available, it will also try to parse each SDF record and report any failures.
"""
import argparse
import sys

def count_sdf_records(path):
    # Simple SDF record splitter: count occurrences of "$$$$" on its own line
    count = 0
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip() == '$$$$':
                count += 1
    return count

def main():
    p = argparse.ArgumentParser(description='Verify SDF conversion from Excel')
    p.add_argument('--input-xlsx', required=True)
    p.add_argument('--sdf', required=True)
    p.add_argument('--smiles-col', default='smiles')
    args = p.parse_args()

    try:
        import pandas as pd
    except Exception as e:
        print('ERROR: pandas is required to read Excel:', e, file=sys.stderr)
        sys.exit(2)

    df = pd.read_excel(args.input_xlsx)
    if args.smiles_col not in df.columns:
        print(f"Warning: smiles column '{args.smiles_col}' not found. Columns: {list(df.columns)}", file=sys.stderr)

    smiles_count = int(df[args.smiles_col].dropna().shape[0]) if args.smiles_col in df.columns else 0
    print(f"Non-null SMILES in Excel: {smiles_count}")

    sdf_count = count_sdf_records(args.sdf)
    print(f"SDF records (counted by $$$$): {sdf_count}")

    if smiles_count != sdf_count:
        print("WARNING: counts differ. Some SMILES may have failed to convert or extra records exist.")
    else:
        print("Counts match.")

    # Optional: try to parse SDF records with RDKit for more detailed failure info
    try:
        from rdkit import Chem
    except Exception:
        print('RDKit not available — skipping per-record parsing checks.')
        return

    # Parse SDF and count failures
    failures = []
    supplier = Chem.SDMolSupplier(args.sdf, removeHs=False)
    parsed = 0
    for i, m in enumerate(supplier):
        if m is None:
            failures.append(i+1)
        else:
            parsed += 1

    print(f"Parsed molecules: {parsed}")
    if failures:
        print(f"Failed to parse {len(failures)} records (1-based indices): {failures[:20]}")
        if len(failures) > 20:
            print("... (truncated)")
    else:
        print('All SDF records parsed by RDKit successfully.')

if __name__ == '__main__':
    main()

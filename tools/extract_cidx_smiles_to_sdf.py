#!/usr/bin/env python3
"""
Read an Excel file with columns including 'CIDX' and 'smiles' and write an SDF using RDKit PandasTools.

Usage:
  python tools/extract_cidx_smiles_to_sdf.py --input input.xlsx --out output.sdf [--smiles-col smiles] [--id-col CIDX]

This script prints helpful guidance if RDKit is not installed.
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Read Excel and write SDF using RDKit PandasTools")
    parser.add_argument("--input", "-i", required=True, help="Input Excel file path")
    parser.add_argument("--out", "-o", required=True, help="Output SDF file path")
    parser.add_argument("--smiles-col", default="smiles", help="Column name containing SMILES (default: smiles)")
    parser.add_argument("--id-col", default="CIDX", help="Column name to use as an identifier/property (default: CIDX)")
    args = parser.parse_args()

    try:
        import pandas as pd
    except Exception as e:
        print("ERROR: pandas is required but could not be imported:", e, file=sys.stderr)
        sys.exit(2)

    try:
        from rdkit.Chem import PandasTools
    except Exception as e:
        print("ERROR: RDKit is required to run this script. Import failed:", e, file=sys.stderr)
        print("If you're using conda, a reliable install command is:\n  conda install -c conda-forge rdkit", file=sys.stderr)
        sys.exit(3)

    # Read Excel
    df = pd.read_excel(args.input)

    # If smiles column missing, try to find one
    if args.smiles_col not in df.columns:
        print(f"Warning: specified smiles column '{args.smiles_col}' not found in Excel. Available columns: {list(df.columns)}", file=sys.stderr)
        # try common alternatives
        for alt in ("smiles", "SMILES", "smile"):
            if alt in df.columns:
                args.smiles_col = alt
                print(f"Using detected smiles column: {alt}", file=sys.stderr)
                break

    # Drop rows with missing smiles
    before = len(df)
    df = df.dropna(subset=[args.smiles_col])
    after = len(df)
    if before != after:
        print(f"Dropped {before-after} rows with missing SMILES")

    # Add RDKit Molecule column
    PandasTools.AddMoleculeColumnToFrame(df, args.smiles_col, 'Molecule')

    # Ensure id column present as property when writing
    properties = list(df.columns)

    PandasTools.WriteSDF(df, args.out, molColName='Molecule', properties=properties)
    print(f"Wrote SDF to {args.out} (rows: {len(df)})")

if __name__ == '__main__':
    main()

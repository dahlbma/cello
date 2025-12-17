#!/usr/bin/env python3
"""
Script to insert control wells (columns 23 and 24) into the config table.
- Column 23: DMSO controls (wells A23..P23)
- Column 24: CTRL controls (wells A24..P24)
"""

import sys
import os

# Add backend directory to path to import config and mydb
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import mydb

# Plate config_ids
PLATE_IDS = ['P111254', 'P111255', 'P111256', 'P111257', 'P111258', 'P111259']

# Row letters (A through P = 16 rows)
ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']

# Control configurations
CONTROLS = [
    {
        'column': '23',
        'compound_id': 'DMSO',
        'notebook_ref': 'DMSO',
        'form': 'DMSO',
        'conc': 10.0,
        'volume': 60.0
    },
    {
        'column': '24',
        'compound_id': 'CTRL',
        'notebook_ref': 'CTRL',
        'form': 'DMSO',
        'conc': 10.0,
        'volume': 60.0
    }
]


def insert_control_wells():
    """Insert control wells into the config table."""
    
    # Connect to database
    conn = mydb.disconnectSafeConnect()
    cursor = conn.cursor()
    
    # Prepare INSERT statement
    insert_sql = """
        INSERT INTO cool.config 
        (config_id, well, compound_id, notebook_ref, FORM, CONC, VOLUME)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    total_inserts = 0
    
    try:
        # For each plate
        for plate_id in PLATE_IDS:
            print(f"Processing plate: {plate_id}")
            
            # For each control type (column 23 and 24)
            for control in CONTROLS:
                # For each row (A through P)
                for row in ROWS:
                    well = f"{row}{control['column']}"
                    
                    # Insert the row
                    cursor.execute(insert_sql, (
                        plate_id,
                        well,
                        control['compound_id'],
                        control['notebook_ref'],
                        control['form'],
                        control['conc'],
                        control['volume']
                    ))
                    
                    total_inserts += 1
                    print(f"  Inserted: {plate_id}, {well}, {control['compound_id']}")
        
        conn.commit()
        print(f"\nSuccessfully inserted {total_inserts} rows!")
        print(f"- {len(PLATE_IDS)} plates")
        print(f"- {len(ROWS)} rows per column")
        print(f"- 2 control columns (23 and 24)")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Inserting control wells into cool.config table")
    print("=" * 60)
    print()
    
    insert_control_wells()
    
    print()
    print("Done!")

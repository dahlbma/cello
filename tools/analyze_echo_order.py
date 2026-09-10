"""Analyze the exact ordering of compound vs BACKFILL rows per plate in an Echo CSV."""
import csv
import re
import sys
from collections import OrderedDict


def normalize_well(well):
    if not well:
        return well
    m = re.match(r'^([A-Za-z]+)(\d+)$', well)
    if m:
        return f"{m.group(1).upper()}{int(m.group(2)):02d}"
    return well


def read_rows(path):
    in_details = False
    headers = None
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '[DETAILS]' in line:
                in_details = True
                continue
            if in_details:
                if not line or line.startswith('['):
                    break
                if headers is None:
                    headers = [h.strip() for h in line.split(',')]
                    continue
                reader = csv.DictReader([line], fieldnames=headers)
                row = next(reader)
                well = row.get('Destination Well', '').strip()
                plate_id = row.get('Destination Plate Barcode', '').strip()
                compound_id = row.get('Sample ID', '').strip()
                if plate_id and well:
                    rows.append({
                        'plate': plate_id,
                        'well': normalize_well(well),
                        'compound': compound_id,
                        'is_backfill': compound_id.upper() == 'BACKFILL',
                    })
    return rows


def main(path):
    rows = read_rows(path)
    print(f"Total detail rows: {len(rows)}")

    # For each plate, find the index range of its compound rows and backfill rows
    for plate in ['P113361', 'P113362']:
        comp_idx = [i for i, r in enumerate(rows) if r['plate'] == plate and not r['is_backfill']]
        back_idx = [i for i, r in enumerate(rows) if r['plate'] == plate and r['is_backfill']]
        print(f"\n=== Plate {plate} ===")
        print(f"  compound rows: {len(comp_idx)}  (index {min(comp_idx)}..{max(comp_idx)})")
        print(f"  backfill rows: {len(back_idx)}  (index {min(back_idx)}..{max(back_idx)})")
        # How many backfill rows appear BEFORE the last compound row?
        last_comp = max(comp_idx)
        back_before_last_comp = [i for i in back_idx if i < last_comp]
        print(f"  backfill rows appearing BEFORE the last compound row (idx<{last_comp}): {len(back_before_last_comp)}")
        # For each backfill row, is its compound row earlier in the file?
        comp_well_to_idx = {}
        for i in comp_idx:
            comp_well_to_idx.setdefault(rows[i]['well'], i)
        backfill_before_compound = 0
        examples = []
        for i in back_idx:
            w = rows[i]['well']
            ci = comp_well_to_idx.get(w)
            if ci is None:
                examples.append((i, w, 'NO-COMP-ROW'))
            elif ci > i:
                backfill_before_compound += 1
                if len(examples) < 10:
                    examples.append((i, w, f'comp@{ci} (AFTER backfill@{i})'))
        print(f"  backfill rows whose compound row comes LATER in file (or missing): {backfill_before_compound}")
        for e in examples:
            print(f"    backfill idx {e[0]} well {e[1]}: {e[2]}")

    # Show a window around the first backfill to see interleaving
    first_back = next(i for i, r in enumerate(rows) if r['is_backfill'])
    print(f"\n--- Window around first backfill (idx {first_back}) ---")
    for i in range(max(0, first_back - 4), min(len(rows), first_back + 8)):
        r = rows[i]
        tag = 'BACKFILL' if r['is_backfill'] else 'compound'
        print(f"  [{i}] {r['plate']} {r['well']} {tag} {r['compound']}")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'frontend/echo_input.csv')
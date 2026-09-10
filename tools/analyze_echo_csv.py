"""Analyze an Echo CSV [DETAILS] section to understand compound vs BACKFILL rows."""
import csv
import sys
from collections import OrderedDict


def normalize_well(well):
    import re
    if not well:
        return well
    m = re.match(r'^([A-Za-z]+)(\d+)$', well)
    if m:
        return f"{m.group(1).upper()}{int(m.group(2)):02d}"
    return well


def main(path):
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

    print(f"Total detail rows: {len(rows)}")

    # Group by plate, preserving order
    plates = OrderedDict()
    for r in rows:
        plates.setdefault(r['plate'], []).append(r)

    for plate, prows in plates.items():
        comp = [r for r in prows if not r['is_backfill']]
        back = [r for r in prows if r['is_backfill']]
        comp_wells = set(r['well'] for r in comp)
        back_wells = set(r['well'] for r in back)
        # backfill wells with no compound row
        missing = back_wells - comp_wells
        # duplicate compound wells
        from collections import Counter
        comp_counts = Counter(r['well'] for r in comp)
        dups = {w: c for w, c in comp_counts.items() if c > 1}
        print(f"\nPlate {plate}: {len(comp)} compound rows, {len(back)} backfill rows")
        print(f"  unique compound wells: {len(comp_wells)}")
        print(f"  unique backfill wells: {len(back_wells)}")
        print(f"  backfill wells MISSING a compound row: {len(missing)}")
        if missing:
            sample = sorted(missing)[:15]
            print(f"    sample missing: {sample}")
        print(f"  compound wells with DUPLICATE rows: {len(dups)}")
        if dups:
            sample = sorted(dups.items())[:15]
            print(f"    sample dups: {sample}")

    # Show the plate order as it appears in the file (first occurrence sequence)
    print("\n--- Plate order in file (transitions) ---")
    prev = None
    transitions = []
    for r in rows:
        if r['plate'] != prev:
            transitions.append(r['plate'])
            prev = r['plate']
    print(" -> ".join(transitions))

    # Show where backfill section starts
    first_backfill_idx = next((i for i, r in enumerate(rows) if r['is_backfill']), None)
    print(f"\nFirst BACKFILL row index: {first_backfill_idx} of {len(rows)}")
    if first_backfill_idx is not None:
        print(f"  row: {rows[first_backfill_idx]}")
        print(f"  previous row: {rows[first_backfill_idx-1]}")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'frontend/echo_input.csv')
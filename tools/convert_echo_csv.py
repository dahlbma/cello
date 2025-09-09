#!/usr/bin/env python3
"""Convert Echo transfer CSV to simplified plate/well compound list.

Usage: python tools/convert_echo_csv.py input.csv -o out.tsv --final-volume 90

Logic:
- Finds the [DETAILS] section, reads the header row, then processes data rows.
- Outputs columns: Plate, Well (A01), Compound Id, Batch, Form, Conc, Volume
- Conc = stock_conc * (transfer_volume / final_volume) where stock_conc comes
  from 'Sample Group' column (if numeric). final_volume defaults to 90.
"""
import csv
import sys
from pathlib import Path
from collections import OrderedDict


def parse_echo_csv(path):
    with open(path, newline='') as fh:
        # iterate until we find the [DETAILS] marker
        reader = csv.reader(fh)
        for row in reader:
            if len(row) and row[0].strip().upper() == '[DETAILS]':
                # next row should be the header
                headers = next(reader)
                return headers, list(reader)
    raise SystemExit('Could not find [DETAILS] section in CSV')


def get_col_index(headers, name):
    try:
        return headers.index(name)
    except ValueError:
        return None


def format_well(w):
    # Convert A1 -> A01, keep letter(s) then zero-pad number to 2 digits
    w = w.strip()
    if not w:
        return ''
    letter = ''.join(ch for ch in w if ch.isalpha())
    num = ''.join(ch for ch in w if ch.isdigit())
    if not num:
        return w
    return f"{letter}{int(num):02d}"


def to_float(s):
    try:
        return float(s)
    except Exception:
        return None


def convert(input_path, output_path, final_volume=90.0, filter_compound_prefix=None):
    headers, rows = parse_echo_csv(input_path)

    # find relevant column indices
    idx_dest_plate = get_col_index(headers, 'Destination Plate Barcode')
    idx_dest_well = get_col_index(headers, 'Destination Well')
    idx_transfer_vol = get_col_index(headers, 'Transfer Volume')
    idx_sample_id = get_col_index(headers, 'Sample ID')
    idx_sample_name = get_col_index(headers, 'Sample Name')
    idx_sample_group = get_col_index(headers, 'Sample Group')
    idx_fluid_type = get_col_index(headers, 'Fluid Type')

    normal_rows = []
    backfill_rows = []
    wells_with_normal = set()

    for r in rows:
        # guard against short rows
        if len(r) < 2:
            continue
        plate = r[idx_dest_plate].strip() if idx_dest_plate is not None and idx_dest_plate < len(r) else ''
        well = r[idx_dest_well].strip() if idx_dest_well is not None and idx_dest_well < len(r) else ''
        transfer_vol = to_float(r[idx_transfer_vol]) if idx_transfer_vol is not None and idx_transfer_vol < len(r) else None
        comp = r[idx_sample_id].strip() if idx_sample_id is not None and idx_sample_id < len(r) else ''
        batch = r[idx_sample_name].strip() if idx_sample_name is not None and idx_sample_name < len(r) else ''
        stock = to_float(r[idx_sample_group]) if idx_sample_group is not None and idx_sample_group < len(r) else None
        form = r[idx_fluid_type].strip() if idx_fluid_type is not None and idx_fluid_type < len(r) else ''

        # optional filter: if a prefix is provided, only include matching compounds
        if filter_compound_prefix and not comp.startswith(filter_compound_prefix):
            # if a prefix is provided, skip others
            continue

        if transfer_vol is None:
            # skip rows without a numeric transfer volume
            continue

        stock_conc = stock if stock is not None else None
        if stock_conc is None:
            # if no stock concentration, assume 1 for relative concentration
            stock_conc = 1.0

        conc = stock_conc * (transfer_vol / float(final_volume))

        well_formatted = format_well(well)
        key = (plate, well_formatted)

        # keep full precision for concentration (do not round/truncate)
        conc_str = repr(conc)
        row_tuple = (plate, well_formatted, comp, batch, form, conc_str, int(final_volume))

        if comp.upper().startswith('BACKFILL'):
            backfill_rows.append((key, row_tuple))
        else:
            normal_rows.append(row_tuple)
            wells_with_normal.add(key)

    # filter backfill rows to only those wells that have normal rows
    filtered_backfill = [r for (key, r) in backfill_rows if key in wells_with_normal]

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # If the output filename indicates an upload format (or user wants it),
    # write the Cello upload CSV layout: Destination Plate Barcode,Destination Well,
    # Sample ID,Sample Name,Fluid Type,Sample Group,Actual Volume
    if out_path.name.lower().startswith('e') and 'cello_upload' in out_path.name.lower() or False:
        # fallback: write upload style if filename looks like the sample
        # (this branch kept for compatibility but we also provide explicit mode below)
        upload = True
    else:
        upload = False

    # default behaviour: write the tab-separated simplified table
    # however, if user passed special flag via global variable set in main, we will write upload CSV
    try:
        from __main__ import UPLOAD_MODE
        if UPLOAD_MODE:
            upload = True
    except Exception:
        pass

    if upload:
        # collect rows preserving original order grouped by plate+well
        wells = []
        well_map = {}
        # use original parse order: normal_rows and backfill_rows were collected
        # but we need exact original order: iterate through rows again
        with open(input_path, newline='') as fh:
            reader = csv.reader(fh)
            # find [DETAILS]
            for row in reader:
                if len(row) and row[0].strip().upper() == '[DETAILS]':
                    headers = next(reader)
                    break
            for row in reader:
                if len(row) < 2:
                    continue
                def get(i):
                    return row[i].strip() if i is not None and i < len(row) else ''

                idx_dest_plate = get_col_index(headers, 'Destination Plate Barcode')
                idx_dest_well = get_col_index(headers, 'Destination Well')
                idx_actual_vol = get_col_index(headers, 'Actual Volume')
                idx_sample_id = get_col_index(headers, 'Sample ID')
                idx_sample_name = get_col_index(headers, 'Sample Name')
                idx_fluid_type = get_col_index(headers, 'Fluid Type')
                idx_sample_group = get_col_index(headers, 'Sample Group')
                idx_transfer_vol = get_col_index(headers, 'Transfer Volume')

                plate = get(idx_dest_plate)
                well = format_well(get(idx_dest_well))
                sample_id = get(idx_sample_id)
                sample_name = get(idx_sample_name)
                fluid_type = get(idx_fluid_type)
                sample_group_raw = get(idx_sample_group)
                actual_vol = get(idx_actual_vol)

                # compute concentration for upload CSV using same logic as TSV
                transfer_vol_val = to_float(get(idx_transfer_vol))
                stock_val = to_float(sample_group_raw)
                stock_conc = stock_val if stock_val is not None else 1.0
                if transfer_vol_val is None:
                    conc_str = ''
                else:
                    conc_val = stock_conc * (transfer_vol_val / float(final_volume))
                    # keep full precision
                    conc_str = repr(conc_val)

                key = (plate, well)
                entry = (plate, well, sample_id, sample_name, fluid_type, conc_str, actual_vol)
                if key not in well_map:
                    well_map[key] = []
                    wells.append(key)
                well_map[key].append(entry)

        # write CSV with header
        with out_path.open('w', newline='') as fh:
            w = csv.writer(fh)
            # match the header format present in E6XX-24008_Cello_Upload_FRANCESCO.csv
            w.writerow(['Plate','Well','Compound Id','Batch','Form','Conc','Volume'])
            for key in wells:
                for entry in well_map[key]:
                    # entry is (plate, well, sample_id, sample_name, fluid_type, conc_str, actual_vol)
                    # map to the desired header ordering
                    plate, well, sample_id, sample_name, fluid_type, conc_str, actual_vol = entry
                    w.writerow([plate, well, sample_id, sample_name, fluid_type, conc_str, actual_vol])
    else:
        with out_path.open('w', newline='') as fh:
            w = csv.writer(fh, delimiter='\t')
            w.writerow(['Plate', 'Well', 'Compound Id', 'Batch', 'Form', 'Conc', 'Volume'])
            # write normal rows first, then backfill rows
            for r in normal_rows:
                # r = (plate, well, comp, batch, form, conc_str, final_volume, transfer_vol)
                w.writerow(r[:7])
            for r in filtered_backfill:
                w.writerow(r[:7])

    # Now create a combined output file where wells that have BACKFILL are merged
    # using Cfinal = (sum(Ci*Vi)) / (sum Vi). The output columns match the original
    # output layout: Plate,Well,Compound Id,Batch,Form,Conc,Volume
    # Build per-well entries from the original input to preserve transfer volumes.
    combined_entries = OrderedDict()
    # prefer Actual Volume column if present, else Transfer Volume
    with open(input_path, newline='') as fh:
        reader = csv.reader(fh)
        for row in reader:
            if len(row) and row[0].strip().upper() == '[DETAILS]':
                headers = next(reader)
                break
        # identify indices
        idx_dest_plate = get_col_index(headers, 'Destination Plate Barcode')
        idx_dest_well = get_col_index(headers, 'Destination Well')
        idx_actual_vol = get_col_index(headers, 'Actual Volume')
        idx_transfer_vol = get_col_index(headers, 'Transfer Volume')
        idx_sample_id = get_col_index(headers, 'Sample ID')
        idx_sample_name = get_col_index(headers, 'Sample Name')
        idx_sample_group = get_col_index(headers, 'Sample Group')
        idx_fluid_type = get_col_index(headers, 'Fluid Type')

        for row in reader:
            if len(row) < 2:
                continue
            def get(i):
                return row[i].strip() if i is not None and i < len(row) else ''

            plate = get(idx_dest_plate)
            well = format_well(get(idx_dest_well))
            sample_id = get(idx_sample_id)
            sample_name = get(idx_sample_name)
            fluid_type = get(idx_fluid_type)
            sample_group_raw = get(idx_sample_group)
            # For aggregation use the aliquot concentration (Sample Group) as Ci
            # and the Transfer Volume as Vi.
            transfer_vol_str = get(idx_transfer_vol)
            transfer_vol_val = to_float(transfer_vol_str)
            stock_val = to_float(sample_group_raw)

            if transfer_vol_val is None:
                # skip rows without numeric transfer volume for aggregation
                continue

            # BACKFILL entries have no compound (DMSO only) -> concentration = 0
            if (sample_id or '').upper().startswith('BACKFILL'):
                conc_val = 0.0
            else:
                conc_val = stock_val if stock_val is not None else 0.0

            key = (plate, well)
            if key not in combined_entries:
                combined_entries[key] = []
            combined_entries[key].append({
                'sample_id': sample_id,
                'sample_name': sample_name,
                'fluid_type': fluid_type,
                'conc': conc_val,
                'vol': transfer_vol_val
            })

    # write combined output file
    stem = out_path.stem
    suffix = out_path.suffix if out_path.suffix else '.tsv'
    combined_path = out_path.with_name(stem + '_combined' + suffix)
    combined_path.parent.mkdir(parents=True, exist_ok=True)

    # choose delimiter based on extension
    combined_delim = ',' if combined_path.suffix.lower() == '.csv' else '\t'
    def fmt_sig3(x):
        # format to 3 significant digits, then tweak to match requested style
        try:
            if x == 0:
                return '0.0'
            s = format(x, '.3g')
        except Exception:
            return repr(x)

        # if scientific notation like '9e-05', make coefficient have a decimal if missing -> '9.0e-05'
        if 'e' in s or 'E' in s:
            parts = s.split('e') if 'e' in s else s.split('E')
            coeff = parts[0]
            exp = parts[1]
            if '.' not in coeff:
                coeff = coeff + '.0'
            return coeff + 'e' + exp

        # if no decimal point and looks like integer, append .0
        if '.' not in s:
            return s + '.0'

        return s
    with combined_path.open('w', newline='') as fh:
        w = csv.writer(fh, delimiter=combined_delim)
        w.writerow(['Plate', 'Well', 'Compound Id', 'Batch', 'Form', 'Conc', 'Volume'])
        # sort by plate then well (letters then numeric part) for predictable ordering
        def well_sort_key_column_major(w):
            letters = ''.join(ch for ch in w if ch.isalpha())
            nums = ''.join(ch for ch in w if ch.isdigit())
            num = int(nums) if nums else 0
            # column-major: sort by numeric part first, then letters
            return (num, letters)

        for plate, well in sorted(combined_entries.keys(), key=lambda k: (k[0], well_sort_key_column_major(k[1]))):
            entries = combined_entries[(plate, well)]
            total_vol = sum(e['vol'] for e in entries if e.get('vol') is not None)
            if total_vol <= 0:
                # skip or write zero-volume row
                continue

            # pick representative compound: prefer first non-BACKFILL
            rep = next((e for e in entries if not (e.get('sample_id') or '').upper().startswith('BACKFILL')), entries[0])
            rep_id = rep.get('sample_id')
            rep_name = rep.get('sample_name')
            rep_form = rep.get('fluid_type')

            # format conc and volume
            total_CV = sum((e.get('conc') or 0.0) * e.get('vol', 0.0) for e in entries)
            cfinal = total_CV / total_vol if total_vol else 0.0

            # format concentration per requested significant-figure rules
            conc_str = fmt_sig3(cfinal)
            vol_str = repr(total_vol)

            w.writerow([plate, well, rep_id, rep_name, rep_form, conc_str, vol_str])


def main(argv):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('input', help='input CSV (Echo transfer file)')
    p.add_argument('-o', '--output', default='out.tsv', help='output TSV path')
    p.add_argument('--final-volume', type=float, default=90.0, help='final volume to compute concentrations (default 90)')
    p.add_argument('--filter-prefix', help='only include compounds starting with this prefix (optional)')
    p.add_argument('--upload', action='store_true', help='write output in Cello upload CSV format')
    args = p.parse_args(argv)

    # export a flag visible to convert()
    global UPLOAD_MODE
    UPLOAD_MODE = bool(args.upload)

    convert(args.input, args.output, final_volume=args.final_volume, filter_compound_prefix=args.filter_prefix)
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main(sys.argv[1:])

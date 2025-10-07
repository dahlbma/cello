#!/usr/bin/env python3
"""
Parse per-batch EBI check responses and collate them into a CSV mapping input CIDX -> response.

Assumptions:
- The input SDF (used to create batches) is available and includes a `CIDX` tag for every molecule.
- The `out_dir` contains files named batch_XXXX.txt in batch order produced by `check_with_ebi.py`.

Output CSV columns:
  CIDX,batch_index,mol_idx_in_batch,status,response_summary

If the EBI response is JSON, the script will try to extract a concise summary field; otherwise it will store a truncated raw response.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import List, Tuple


def iter_sdf_cidx(path: Path):
    """Yield CIDX tags in order from an SDF file. If a molecule lacks CIDX, yield None."""
    cidxs: List[str] = []
    buf: List[str] = []
    with path.open('r', encoding='utf-8', errors='replace') as inf:
        for line in inf:
            buf.append(line)
            if line.strip() == '$$$$':
                # parse buf for >  <CIDX> tag
                cidx = None
                for i, l in enumerate(buf):
                    if l.startswith('>') and 'CIDX' in l:
                        # next non-empty line is the value
                        if i + 1 < len(buf):
                            val = buf[i+1].strip()
                            if val:
                                cidx = val
                        break
                cidxs.append(cidx)
                buf = []
    if buf:
        # final record without $$$$
        cidx = None
        for i, l in enumerate(buf):
            if l.startswith('>') and 'CIDX' in l:
                if i + 1 < len(buf):
                    val = buf[i+1].strip()
                    if val:
                        cidx = val
                break
        cidxs.append(cidx)
    for c in cidxs:
        yield c


def parse_response_file(path: Path):
    """Try to parse the response file. If JSON, return a list of per-molecule summaries; otherwise return raw text in one-item list."""
    txt = path.read_text(encoding='utf-8', errors='replace')
    # try JSON
    try:
        doc = json.loads(txt)
        # if it's a list, return list of summaries
        if isinstance(doc, list):
            return [json.dumps(x) for x in doc]
        # if it's a dict with per-molecule info, try to extract
        if isinstance(doc, dict):
            # try common keys
            if 'result' in doc and isinstance(doc['result'], list):
                return [json.dumps(x) for x in doc['result']]
            # fallback: single summary
            return [json.dumps(doc)]
    except Exception:
        pass
    # non-JSON: return raw text truncated
    return [txt.strip()]


def main():
    p = argparse.ArgumentParser(description='Parse EBI batch responses and map them to input CIDX values')
    p.add_argument('--input-sdf', default='tools/COMPOUND_CTAB_out.sdf', help='Input SDF used to create batches')
    p.add_argument('--out-dir', default='tools/ebi_checks', help='Directory containing batch_XXXX.txt files')
    p.add_argument('--batch-size', type=int, default=100, help='Batch size used when creating responses')
    p.add_argument('--output-csv', default='tools/ebi_summary.csv', help='Output CSV path')
    args = p.parse_args()

    input_sdf = Path(args.input_sdf)
    out_dir = Path(args.out_dir)
    out_csv = Path(args.output_csv)

    if not input_sdf.exists():
        print('Input SDF not found:', input_sdf)
        return
    if not out_dir.exists():
        print('Out dir not found:', out_dir)
        return

    # read cidxs
    cidxs = list(iter_sdf_cidx(input_sdf))
    total_mols = len(cidxs)
    # build list of batch files in order
    files = sorted(out_dir.glob('batch_*.txt'))
    rows = []
    mol_ptr = 0
    for batch_index, f in enumerate(files, start=1):
        resp_items = parse_response_file(f)
        # If the response is a single item but our batch has multiple molecules,
        # we'll assign the same response to all molecules in the batch (fallback).
        for i in range(args.batch_size):
            if mol_ptr >= total_mols:
                break
            cidx = cidxs[mol_ptr]
            # determine response for this molecule
            if len(resp_items) == args.batch_size:
                summary = resp_items[i]
            elif len(resp_items) > 1 and len(resp_items) == len(resp_items):
                # weird case - try to use i if possible
                summary = resp_items[i] if i < len(resp_items) else resp_items[0]
            else:
                summary = resp_items[0]
            # trim very long summaries
            if len(summary) > 1000:
                summary = summary[:1000] + '...'
            rows.append((cidx or '', batch_index, i+1, summary))
            mol_ptr += 1

    # If there are remaining molecules not covered by files, mark as MISSING
    while mol_ptr < total_mols:
        cidx = cidxs[mol_ptr]
        rows.append((cidx or '', None, None, 'MISSING_RESPONSE'))
        mol_ptr += 1

    # write CSV
    with out_csv.open('w', newline='', encoding='utf-8') as outf:
        w = csv.writer(outf)
        w.writerow(['CIDX', 'batch_index', 'mol_idx_in_batch', 'response_summary'])
        for r in rows:
            w.writerow(r)

    print(f'Wrote summary CSV with {len(rows)} rows to {out_csv}')


if __name__ == '__main__':
    main()

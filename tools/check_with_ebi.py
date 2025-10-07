#!/usr/bin/env python3
"""
Chunk an SDF into batches and submit each batch to the EBI ChEMBL /utils/check endpoint.

Behavior:
- Reads an input SDF and groups molecules into batches of `batch_size` (default 100).
- Writes each batch to a single temp file (overwritten each iteration).
- Posts the temp file using curl to https://www.ebi.ac.uk/chembl/api/utils/check and saves the response
  to an output directory as batch_{i}.txt.

Usage example:
  python3 tools/check_with_ebi.py --input tools/COMPOUND_CTAB_out.sdf --batch-size 100 \
      --temp-file tools/_chunk.sdf --out-dir tools/ebi_checks

The script includes a --dry-run flag that skips the network call (useful for testing).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List
import json
from rdkit import Chem


def iter_sdf_records(path: Path):
    """Yield SDF records (strings) from the file at path. Each record ends with '$$$$' line."""
    buf: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as inf:
        for line in inf:
            buf.append(line)
            if line.strip() == "$$$$":
                yield "".join(buf)
                buf = []
    # if file didn't end with $$$$, yield last buffer
    if buf:
        yield "".join(buf)


def extract_stereo_mismatch_indices(ebi_response_text: str, batch_size: int) -> List[int]:
    """Return 0-based indices of molecules in the batch that reported an InChi_Mol/RDKit stereo mismatch.

    The EBI response can be JSON (list or dict). We look for occurrences of the string
    'InChi_Mol/RDKit stereo mismatch' in the per-molecule messages. If the response is not
    per-molecule, return an empty list.
    """
    idxs: List[int] = []
    # try JSON parse first
    try:
        doc = json.loads(ebi_response_text)
    except Exception:
        doc = None

    def check_msg(msg: str, idx: int):
        if not msg:
            return False
        if 'InChi_Mol/RDKit stereo mismatch' in msg:
            return True
        # some responses include the phrase without exact spacing
        if 'InChi_Mol/RDKit' in msg and 'stereo' in msg:
            return True
        return False

    if isinstance(doc, list):
        for i, item in enumerate(doc):
            try:
                s = json.dumps(item) if not isinstance(item, str) else item
            except Exception:
                s = str(item)
            if check_msg(s, i):
                idxs.append(i)
    elif isinstance(doc, dict):
        # try to find a 'result' list or other list-like payload
        for key in ('result', 'items', 'errors'):
            if key in doc and isinstance(doc[key], list):
                for i, item in enumerate(doc[key]):
                    s = json.dumps(item) if not isinstance(item, str) else item
                    if check_msg(s, i):
                        idxs.append(i)
                break
    else:
        # fallback: search raw text for line markers like '[i, "Message"]' -> crude
        # find occurrences of the stereo mismatch phrase; attempt to extract nearby index
        txt = ebi_response_text
        if 'InChi_Mol/RDKit stereo mismatch' in txt:
            # naive: if the response is a JSON-like list of [index, message], try to parse
            try:
                doc2 = json.loads(txt)
                if isinstance(doc2, list):
                    for i, item in enumerate(doc2):
                        if isinstance(item, list) and len(item) >= 2 and isinstance(item[1], str):
                            if 'InChi_Mol/RDKit' in item[1] and 'stereo' in item[1]:
                                idxs.append(int(item[0]))
            except Exception:
                pass

    # ensure indices are within batch bounds
    idxs = [i for i in idxs if 0 <= i < batch_size]
    return sorted(set(idxs))


def clear_stereo_in_sdf(sdf_path: Path, indices_to_clear: List[int], out_dir: Path) -> List[Path]:
    """Clear stereochemistry for given 0-based indices in the SDF file.

    Overwrites the sdf_path with modified records. Also saves individual cleared molfiles
    into out_dir with names derived from the record's CIDX tag when present, falling back
    to batch-indexed names. Returns a list of saved file Paths.
    """
    saved_files: List[Path] = []
    if not indices_to_clear:
        return saved_files
    records = list(iter_sdf_records(sdf_path))
    out_dir.mkdir(parents=True, exist_ok=True)
    # helper to extract properties after molblock
    def split_record(rec: str):
        # robust splitting: find 'M  END' line which marks end of molblock
        lines = rec.splitlines(keepends=True)
        m_end_idx = None
        for i, ln in enumerate(lines):
            if ln.strip() == 'M  END':
                m_end_idx = i
                break
        if m_end_idx is not None:
            molblock = ''.join(lines[: m_end_idx + 1])
            props = ''.join(lines[m_end_idx + 1 :])
            # strip trailing record terminator from props
            if props.endswith('$$$$\n'):
                props = props[: -5]
            return molblock, props

        # fallback: look for a property-marker line '>  <' which begins property block
        for i, ln in enumerate(lines):
            if ln.startswith('>') and '<' in ln:
                molblock = ''.join(lines[:i])
                props = ''.join(lines[i:])
                if props.endswith('$$$$\n'):
                    props = props[:-5]
                return molblock, props

        # if no markers, split at first '$$$$' if present
        if '$$$$' in rec:
            molblock, _, rest = rec.partition('$$$$')
            return molblock + '\n', rest
        return rec, ''

    changed_any = False
    for idx in indices_to_clear:
        if idx < 0 or idx >= len(records):
            continue
        rec = records[idx]
        molblock, props = split_record(rec)
        try:
            m = Chem.MolFromMolBlock(molblock, sanitize=False, removeHs=False)
            if m is None:
                continue
            # clear stereo
            for at in m.GetAtoms():
                at.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
                if at.HasProp('_CIPCode'):
                    try:
                        at.ClearProp('_CIPCode')
                    except Exception:
                        pass
            for b in m.GetBonds():
                if b.HasProp('_MolFileBondStereo'):
                    try:
                        b.ClearProp('_MolFileBondStereo')
                    except Exception:
                        pass
                # clear any directional or stereochemical bond markings
                b.SetBondDir(Chem.BondDir.NONE)
                try:
                    b.SetStereo(Chem.BondStereo.STEREONONE)
                except Exception:
                    # older RDKit versions may not have STEREONONE, fall back to STEREOANY->NONE via clear
                    try:
                        b.SetStereo(Chem.BondStereo.STEREOANY)
                    except Exception:
                        pass
            newblock = Chem.MolToMolBlock(m)
            # reconstruct record preserving props
            newrec = newblock
            if props:
                # ensure props begin with newline
                if not props.startswith('\n') and not props.startswith('\r'):
                    newrec += '\n'
                newrec += props
            # ensure record ends with $$$$
            if not newrec.strip().endswith('$$$$'):
                if not newrec.endswith('\n'):
                    newrec += '\n'
                newrec += '$$$$\n'
            records[idx] = newrec
            changed_any = True
            # attempt to get CIDX from props to name saved molfile
            cidx = None
            if props:
                # look for a >  <CIDX> tag
                prop_lines = props.splitlines()
                for i, pl in enumerate(prop_lines):
                    if pl.startswith('>') and 'CIDX' in pl:
                        # next non-empty line is value
                        if i + 1 < len(prop_lines):
                            val = prop_lines[i + 1].strip()
                            if val:
                                cidx = val
                        break
            if not cidx:
                cleared_name = f"cleared_{idx:05d}.mol"
                orig_name = f"orig_{idx:05d}.mol"
            else:
                # sanitize filename
                safe = ''.join([c for c in cidx if c.isalnum() or c in ('_', '-')])
                cleared_name = f"{safe}_cleared.mol"
                orig_name = f"{safe}_orig.mol"

            orig_target = out_dir / orig_name
            # write original molfile including props so ID tags are preserved
            if props:
                if molblock.endswith('\n'):
                    orig_content = molblock + props
                else:
                    orig_content = molblock + '\n' + props
            else:
                orig_content = molblock
            try:
                orig_target.write_text(orig_content, encoding='utf-8')
            except Exception:
                pass

            # write cleared molfile including props
            if props:
                if newblock.endswith('\n'):
                    cleared_content = newblock + props
                else:
                    cleared_content = newblock + '\n' + props
            else:
                cleared_content = newblock

            cleared_target = out_dir / cleared_name
            cleared_target.write_text(cleared_content, encoding='utf-8')
            saved_files.append(cleared_target)
        except Exception:
            continue

    if changed_any:
        with sdf_path.open('w', encoding='utf-8') as outf:
            for r in records:
                # each record should already include $$$$
                outf.write(r)

    return saved_files


def write_batch(records: List[str], temp_path: Path):
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with temp_path.open("w", encoding="utf-8") as outf:
        for rec in records:
            outf.write(rec)


def call_ebi_check(temp_path: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    """Call the EBI check endpoint using curl and return CompletedProcess."""
    cmd = [
        "curl",
        "-sS",
        "-X",
        "POST",
        "-F",
        f"file=@{str(temp_path)}",
        "https://www.ebi.ac.uk/chembl/api/utils/check",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def main():
    p = argparse.ArgumentParser(description="Chunk an SDF and check each chunk with EBI ChEMBL service")
    p.add_argument("--input", default="tools/COMPOUND_CTAB_out.sdf", help="Input SDF path")
    p.add_argument("--batch-size", type=int, default=100, help="Number of molecules per batch")
    p.add_argument("--temp-file", default="tools/_chunk.sdf", help="Temp file path to reuse for each batch")
    p.add_argument("--out-dir", default="tools/ebi_checks", help="Directory to store per-batch responses")
    p.add_argument("--dry-run", action="store_true", help="Do not call network; only write batches")
    p.add_argument("--sleep", type=float, default=3.0, help="Seconds to sleep between calls (rate-limit)")
    p.add_argument("--output-csv", default=None, help="If provided, run the parser and write the final CSV to this path")
    p.add_argument("--auto-fix-stereo", action="store_true", help="If EBI reports InChi_Mol/RDKit stereo mismatch for molecules in a batch, clear their stereo and resubmit the batch once")
    args = p.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    temp_path = Path(args.temp_file)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    batch: List[str] = []
    total = 0
    batch_index = 0
    records_iter = iter_sdf_records(input_path)

    for rec in records_iter:
        batch.append(rec)
        total += 1
        if len(batch) >= args.batch_size:
            batch_index += 1
            print(f"Processing batch {batch_index}: molecules {total - len(batch) + 1}..{total}")
            write_batch(batch, temp_path)
            if not args.dry_run:
                proc = call_ebi_check(temp_path)
                out_file = out_dir / f"batch_{batch_index:04d}.txt"
                with out_file.open("w", encoding="utf-8") as of:
                    of.write(proc.stdout)
                    if proc.stderr:
                        of.write("\n--- STDERR ---\n")
                        of.write(proc.stderr)
                if proc.returncode != 0:
                    print(f"Warning: curl returned non-zero exit status {proc.returncode} for batch {batch_index}")
                # optionally attempt to auto-fix stereo mismatches reported by EBI
                if args.auto_fix_stereo and proc.returncode == 0:
                    try:
                        idxs = extract_stereo_mismatch_indices(proc.stdout, args.batch_size)
                        if idxs:
                            print(f"Auto-fix: clearing stereo for {len(idxs)} molecules in batch {batch_index}: indices {idxs}")
                            # clear stereo in the temp SDF for these indices and resubmit once
                            saved = clear_stereo_in_sdf(temp_path, idxs, out_dir)
                            if saved:
                                print(f"Saved cleared molfiles: {', '.join([str(p.name) for p in saved])}")
                                proc2 = call_ebi_check(temp_path)
                                out_file_fixed = out_dir / f"batch_{batch_index:04d}_fixed.txt"
                                with out_file_fixed.open("w", encoding="utf-8") as of2:
                                    of2.write(proc2.stdout)
                                    if proc2.stderr:
                                        of2.write("\n--- STDERR ---\n")
                                        of2.write(proc2.stderr)
                                if proc2.returncode != 0:
                                    print(f"Warning: retry curl returned non-zero exit status {proc2.returncode} for batch {batch_index}")
                                else:
                                    # overwrite the original batch file so downstream parsing uses the fixed results
                                    try:
                                        with out_file.open("w", encoding="utf-8") as of:
                                            of.write(proc2.stdout)
                                            if proc2.stderr:
                                                of.write("\n--- STDERR ---\n")
                                                of.write(proc2.stderr)
                                    except Exception:
                                        pass
                    except Exception as e:
                        print(f"Warning: auto-fix-stereo failed for batch {batch_index}: {e}")
            else:
                # dry-run: save the batch to a sample output file for inspection
                out_file = out_dir / f"batch_{batch_index:04d}.txt"
                with out_file.open("w", encoding="utf-8") as of:
                    of.write(f"DRYRUN: batch {batch_index} with {len(batch)} records written to {temp_path}\n")
            batch = []
            # reuse same temp file; optional small sleep
            time.sleep(args.sleep)

    # last partial batch
    if batch:
        batch_index += 1
        print(f"Processing final batch {batch_index}: molecules {total - len(batch) + 1}..{total}")
        write_batch(batch, temp_path)
        if not args.dry_run:
            proc = call_ebi_check(temp_path)
            out_file = out_dir / f"batch_{batch_index:04d}.txt"
            with out_file.open("w", encoding="utf-8") as of:
                of.write(proc.stdout)
                if proc.stderr:
                    of.write("\n--- STDERR ---\n")
                    of.write(proc.stderr)
            if proc.returncode != 0:
                print(f"Warning: curl returned non-zero exit status {proc.returncode} for batch {batch_index}")
            # final-batch auto-fix similar to above
            if args.auto_fix_stereo and proc.returncode == 0:
                try:
                    idxs = extract_stereo_mismatch_indices(proc.stdout, args.batch_size)
                    if idxs:
                        print(f"Auto-fix: clearing stereo for {len(idxs)} molecules in final batch {batch_index}: indices {idxs}")
                        saved = clear_stereo_in_sdf(temp_path, idxs, out_dir)
                        if saved:
                            print(f"Saved cleared molfiles: {', '.join([str(p.name) for p in saved])}")
                            proc2 = call_ebi_check(temp_path)
                            out_file_fixed = out_dir / f"batch_{batch_index:04d}_fixed.txt"
                            with out_file_fixed.open("w", encoding="utf-8") as of2:
                                of2.write(proc2.stdout)
                                if proc2.stderr:
                                    of2.write("\n--- STDERR ---\n")
                                    of2.write(proc2.stderr)
                            if proc2.returncode != 0:
                                print(f"Warning: retry curl returned non-zero exit status {proc2.returncode} for final batch {batch_index}")
                            else:
                                # ensure parser picks up the fixed response instead of the original
                                try:
                                    with out_file.open("w", encoding="utf-8") as of:
                                        of.write(proc2.stdout)
                                        if proc2.stderr:
                                            of.write("\n--- STDERR ---\n")
                                            of.write(proc2.stderr)
                                except Exception:
                                    pass
                except Exception as e:
                    print(f"Warning: auto-fix-stereo failed for final batch {batch_index}: {e}")
        else:
            out_file = out_dir / f"batch_{batch_index:04d}.txt"
            with out_file.open("w", encoding="utf-8") as of:
                of.write(f"DRYRUN: batch {batch_index} with {len(batch)} records written to {temp_path}\n")

    print(f"Done: total molecules {total}, total batches {batch_index}")
    print(f"Per-batch outputs saved to: {out_dir}")

    # optionally run the parser to collate per-molecule results into a CSV
    if args.output_csv:
        parser = Path(__file__).parent / 'parse_ebi_responses.py'
        if not parser.exists():
            print(f"Parser script not found: {parser}; cannot produce CSV")
            return
        cmd = [
            sys.executable,
            str(parser),
            '--input-sdf', str(input_path),
            '--out-dir', str(out_dir),
            '--batch-size', str(args.batch_size),
            '--output-csv', str(args.output_csv),
        ]
        print('Running parser to produce CSV:', args.output_csv)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            print('Parser failed:')
            print(proc.stdout)
            print(proc.stderr)
        else:
            print(proc.stdout)
            print('CSV written to', args.output_csv)


if __name__ == '__main__':
    main()

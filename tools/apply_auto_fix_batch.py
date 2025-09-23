#!/usr/bin/env python3
"""Extract stereo-mismatch indices from an EBI batch response and save cleared molfiles.

Usage:
  python3 tools/apply_auto_fix_batch.py --batch-file tools/ebi_checks/batch_0024.txt \
      --input-sdf tools/COMPOUND_CTAB_out.sdf --batch-index 24 --batch-size 100 --out-dir tools/ebi_checks

This will save per-molecule cleared molfiles named <CIDX>_cleared.mol (or cleared_#####.mol)
into the out-dir.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

# rdkit is optional for this helper; we'll import it lazily and handle ImportError
Chem = None


def iter_sdf_records(path: Path):
    buf: List[str] = []
    with path.open('r', encoding='utf-8', errors='replace') as inf:
        for line in inf:
            buf.append(line)
            if line.strip() == '$$$$':
                yield ''.join(buf)
                buf = []
    if buf:
        yield ''.join(buf)


def extract_stereo_mismatch_indices_from_text(txt: str, batch_size: int) -> List[int]:
    idxs: List[int] = []
    try:
        doc = json.loads(txt)
    except Exception:
        doc = None

    def check_msg(msg: str) -> bool:
        if not msg:
            return False
        if 'InChi_Mol/RDKit stereo mismatch' in msg:
            return True
        if 'InChi_Mol/RDKit' in msg and 'stereo' in msg:
            return True
        return False

    if isinstance(doc, list):
        for i, item in enumerate(doc):
            s = json.dumps(item) if not isinstance(item, str) else item
            if check_msg(s):
                idxs.append(i)
    elif isinstance(doc, dict):
        for key in ('result', 'items', 'errors'):
            if key in doc and isinstance(doc[key], list):
                for i, item in enumerate(doc[key]):
                    s = json.dumps(item) if not isinstance(item, str) else item
                    if check_msg(s):
                        idxs.append(i)
                break
    else:
        if 'InChi_Mol/RDKit stereo mismatch' in txt:
            try:
                doc2 = json.loads(txt)
                if isinstance(doc2, list):
                    for item in doc2:
                        if isinstance(item, list) and len(item) >= 2 and isinstance(item[1], str):
                            if 'InChi_Mol/RDKit' in item[1] and 'stereo' in item[1]:
                                idxs.append(int(item[0]))
            except Exception:
                pass
    return [i for i in sorted(set(idxs)) if 0 <= i < batch_size]


def split_record_preserve(rec: str):
    lines = rec.splitlines(keepends=True)
    m_end_idx = None
    for i, ln in enumerate(lines):
        if ln.strip() == 'M  END':
            m_end_idx = i
            break
    if m_end_idx is not None:
        molblock = ''.join(lines[: m_end_idx + 1])
        props = ''.join(lines[m_end_idx + 1 :])
        if props.endswith('$$$$\n'):
            props = props[:-5]
        return molblock, props
    for i, ln in enumerate(lines):
        if ln.startswith('>') and '<' in ln:
            molblock = ''.join(lines[:i])
            props = ''.join(lines[i:])
            if props.endswith('$$$$\n'):
                props = props[:-5]
            return molblock, props
    if '$$$$' in rec:
        molblock, _, rest = rec.partition('$$$$')
        return molblock + '\n', rest
    return rec, ''


def clear_stereo_and_save(molblock: str, props: str, out_dir: Path, idx: int):
    """Save the original molfile and a stereo-cleared molfile.

    Returns a tuple (orig_path, cleared_path).
    """
    # find CIDX in props first so both files can be named consistently
    cidx = None
    if props:
        prop_lines = props.splitlines()
        for i, pl in enumerate(prop_lines):
            if pl.startswith('>') and 'CIDX' in pl:
                if i + 1 < len(prop_lines):
                    val = prop_lines[i + 1].strip()
                    if val:
                        cidx = val
                break

    if cidx:
        safe = ''.join([c for c in cidx if c.isalnum() or c in ('_', '-')])
        orig_name = f"{safe}_orig.mol"
        cleared_name = f"{safe}_cleared.mol"
    else:
        orig_name = f"orig_{idx:05d}.mol"
        cleared_name = f"cleared_{idx:05d}.mol"

    orig_target = out_dir / orig_name
    # write the original molfile: molblock plus the SDF property block (so ID tags are preserved)
    if props:
        # ensure separation between molblock and props
        if molblock.endswith('\n'):
            orig_content = molblock + props
        else:
            orig_content = molblock + '\n' + props
    else:
        orig_content = molblock
    orig_target.write_text(orig_content, encoding='utf-8')

    # Attempt to clear stereo using RDKit if available
    global Chem
    if Chem is None:
        try:
            from rdkit import Chem as _Chem
            Chem = _Chem  # type: ignore
        except Exception:
            # RDKit not available; write only the original molfile and return None for cleared
            return orig_target, None

    m = Chem.MolFromMolBlock(molblock, sanitize=False, removeHs=False)
    if m is None:
        raise ValueError('RDKit could not parse molblock')
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
        b.SetBondDir(Chem.BondDir.NONE)
        try:
            b.SetStereo(Chem.BondStereo.STEREONONE)
        except Exception:
            try:
                b.SetStereo(Chem.BondStereo.STEREOANY)
            except Exception:
                pass
    newblock = Chem.MolToMolBlock(m)

    # append the same props to the cleared molfile so the CIDX / metadata remain available
    if props:
        if newblock.endswith('\n'):
            cleared_content = newblock + props
        else:
            cleared_content = newblock + '\n' + props
    else:
        cleared_content = newblock

    cleared_target = out_dir / cleared_name
    cleared_target.write_text(cleared_content, encoding='utf-8')
    return orig_target, cleared_target


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--batch-file', required=True)
    p.add_argument('--input-sdf', required=True)
    p.add_argument('--batch-index', type=int, required=True)
    p.add_argument('--batch-size', type=int, default=100)
    p.add_argument('--out-dir', default='tools/ebi_checks')
    args = p.parse_args()

    batch_file = Path(args.batch_file)
    input_sdf = Path(args.input_sdf)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not batch_file.exists():
        print('Batch file not found:', batch_file)
        return
    if not input_sdf.exists():
        print('Input SDF not found:', input_sdf)
        return

    txt = batch_file.read_text(encoding='utf-8', errors='replace')
    idxs = extract_stereo_mismatch_indices_from_text(txt, args.batch_size)
    print('Detected stereo-mismatch indices in batch (0-based):', idxs)
    if not idxs:
        print('No stereo mismatches detected; nothing to save')
        return

    # extract batch records from input sdf
    start = (args.batch_index - 1) * args.batch_size
    end = start + args.batch_size
    records = list(iter_sdf_records(input_sdf))
    if start >= len(records):
        print('Batch start beyond end of input SDF')
        return
    batch_records = records[start:end]
    # write temp batch file
    temp = Path('tools/_chunk_fix.sdf')
    with temp.open('w', encoding='utf-8') as outf:
        for r in batch_records:
            outf.write(r)

    saved = []
    for local_idx in idxs:
        if local_idx < 0 or local_idx >= len(batch_records):
            continue
        rec = batch_records[local_idx]
        molblock, props = split_record_preserve(rec)
        try:
            orig_path, cleared_path = clear_stereo_and_save(molblock, props, out_dir, local_idx)
            saved.append((orig_path, cleared_path))
            print('Saved original molfile:', orig_path)
            print('Saved cleared molfile:  ', cleared_path)
        except Exception as e:
            print('Failed to save cleared molfile for index', local_idx, 'error:', e)

    if not saved:
        print('No files saved')
    else:
        print('Saved files:')
        for orig_path, cleared_path in saved:
            print(' - orig:   ', orig_path)
            print('   cleared:', cleared_path)


if __name__ == '__main__':
    main()

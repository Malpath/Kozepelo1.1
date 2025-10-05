#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from decimal import Decimal, ROUND_HALF_EVEN
from collections import OrderedDict, Counter

SEP_RE = re.compile(r"^=+")

def is_sep(line: str) -> bool:
    return SEP_RE.match(line) is not None

# =========================
# STEP1
# =========================
def process_section(lines):
    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("U "):
            output_lines.append(line.rstrip())
            j = i + 1
            while j < len(lines) and not lines[j].startswith("A "):
                output_lines.append(lines[j].rstrip())
                j += 1
            if j < len(lines) and lines[j].startswith("A "):
                j += 1  # skip orientation A line

            blocks_by_id = OrderedDict()
            current_block = []
            current_id = None

            while j < len(lines) and not lines[j].startswith("U "):
                l = lines[j].rstrip()
                if l.startswith("A "):
                    pid = l.split()[1] if len(l.split()) > 1 else "UNKNOWN"
                    if current_id is None:
                        current_id = pid
                        current_block = [l]
                    elif pid == current_id:
                        current_block.append(l)
                    else:
                        if current_id not in blocks_by_id:
                            blocks_by_id[current_id] = []
                        blocks_by_id[current_id].append(current_block)
                        current_id = pid
                        current_block = [l]
                else:
                    if current_block:
                        if current_id not in blocks_by_id:
                            blocks_by_id[current_id] = []
                        blocks_by_id[current_id].append(current_block)
                        current_block = []
                        current_id = None
                    output_lines.append(l)
                j += 1

            if current_block:
                if current_id not in blocks_by_id:
                    blocks_by_id[current_id] = []
                blocks_by_id[current_id].append(current_block)

            for pid, blist in blocks_by_id.items():
                for block in blist:
                    for b in block:
                        output_lines.append(b)
                    output_lines.append("")

            i = j
        else:
            output_lines.append(line.rstrip())
            i += 1
    return output_lines

def step1(infile):
    with open(infile, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    sections = []
    current = []
    for line in lines:
        if is_sep(line):
            if current:
                sections.append(current)
                current = []
            sections.append([line.rstrip()])
        else:
            current.append(line)
    if current:
        sections.append(current)

    output_lines = []
    for sec in sections:
        if sec and is_sep(sec[0]):
            output_lines.extend(sec)
        else:
            output_lines.extend(process_section(sec))

    return "\n".join(output_lines)

# =========================
# SEGÉDFÜGGVÉNYEK
# =========================
def avg_distance(values):
    vals = [Decimal(str(v)) for v in values]
    mean = sum(vals) / len(vals)
    return mean.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)

def replace_distance(line, new_val):
    """Csak az 5. oszlop értékét írja át, megtartva a spacinget."""
    parts = line.split()
    if len(parts) > 4:
        old_val = parts[4]
        idx = line.find(old_val)
        if idx >= 0:
            new_str = f"{new_val:.4f}".rjust(len(old_val))
            return line[:idx] + new_str + line[idx+len(old_val):]
    return line

def similar(a, b, tol=1.0):
    try:
        return abs(float(a) - float(b)) <= tol or abs(abs(float(a)-float(b)) - 360.0) <= tol
    except:
        return False

# =========================
# STEP2A
# =========================
def step2a(infile):
    with open(infile, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip("\n") for l in f]

    out = []
    i = 0
    while i < len(lines):
        l1 = lines[i]
        if l1.startswith("A ") and i+1 < len(lines) and lines[i+1].startswith("A "):
            l2 = lines[i+1]
            p1, p2 = l1.split(), l2.split()
            if len(p1) > 4 and len(p2) > 4 and p1[1] == p2[1] and \
               similar(p1[2], p2[2], 1.0) and similar(p1[3], p2[3], 1.0):
                d1, d2 = float(p1[4]), float(p2[4])
                avgd = avg_distance([d1, d2])
                new_line = replace_distance(l1, avgd)  # mindig az első sor marad
                out.append(new_line)
                i += 2
                continue
        out.append(l1)
        i += 1

    # üres sor szabály
    lines2 = [ln for ln in out if ln.strip()]
    final = []
    i = 0
    while i < len(lines2)-1:
        cur = lines2[i]
        nxt = lines2[i+1]
        if cur.startswith("A ") and nxt.startswith("A "):
            id1, id2 = cur.split()[1], nxt.split()[1]
            if id1 == id2:
                final.append(cur)
                final.append(nxt)
                final.append("")
                i += 2
                continue
            else:
                final.append(cur)
                final.append("")
                final.append(nxt)
                i += 2
                continue
        else:
            final.append(cur)
            i += 1
    if i == len(lines2)-1:
        final.append(lines2[i])

    return "\n".join(final)

# =========================
# STEP2B
# =========================
def process_section_lines(section_lines):
    seq = []
    cur_block = []
    for ln in section_lines:
        if ln.startswith("A "):
            cur_block.append(ln)
        else:
            if cur_block:
                seq.append(("block", cur_block))
                cur_block = []
            seq.append(("line", ln))
    if cur_block:
        seq.append(("block", cur_block))

    ids = []
    for kind, item in seq:
        if kind == "block" and item:
            pid = item[0].split()[1] if len(item[0].split()) > 1 else "UNKNOWN"
            ids.append(pid)
    counts = Counter(ids)

    out_lines = []
    for kind, item in seq:
        if kind == "line":
            out_lines.append(item)
        else:
            block = item
            pid = block[0].split()[1] if len(block[0].split()) > 1 else "UNKNOWN"
            if counts[pid] <= 1:
                out_lines.extend(block)
            else:
                dists = []
                for l in block:
                    ps = l.split()
                    if len(ps) > 4:
                        try:
                            dists.append(float(ps[4]))
                        except:
                            pass
                if dists:
                    avgd = avg_distance(dists)
                    new_first = replace_distance(block[0], avgd)
                    out_lines.append(new_first)
                else:
                    out_lines.append(block[0])
    return out_lines

def step2b(infile):
    with open(infile, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

    out = []
    section = []
    for ln in lines:
        if ln.startswith("="):
            if section:
                out.extend(process_section_lines(section))
                section = []
            out.append(ln)
        else:
            section.append(ln)
    if section:
        out.extend(process_section_lines(section))

    out = [l for l in out if l.strip()]  # töröljük az üreseket
    return "\n".join(out)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Használat: python3 feldolgozo_grouped.py <infile> <step1|step2a|step2b>")
        sys.exit(0)

    infile = sys.argv[1]
    step = sys.argv[2]

    if step == "step1":
        print(step1(infile))
    elif step == "step2a":
        print(step2a(infile))
    elif step == "step2b":
        print(step2b(infile))
    else:
        print(f"Ismeretlen lépés: {step}")

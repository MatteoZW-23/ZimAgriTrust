#!/usr/bin/env python3
"""Spec-coverage tool.

Scans the codebase for `F#NNN` traceability markers and reports which of the
348 functions in `docs/SYSTEM_SPECIFICATION.md` are referenced in source.

Usage:
    python scripts/spec_coverage.py                 # summary
    python scripts/spec_coverage.py --missing       # list IDs with no source ref
    python scripts/spec_coverage.py --by-category   # tabular by spec section
    python scripts/spec_coverage.py --json          # machine-readable

Exit code is non-zero if --fail-under is given and coverage is below it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_FUNCTIONS = list(range(1, 349))  # 1..348

SCAN_DIRS = ["backend/app", "apps", "tests"]
SCAN_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".md"}
EXCLUDE_PARTS = {"node_modules", "__pycache__", ".venv", "dist", "build", ".git"}

MARKER_RE = re.compile(r"F#(\d{1,3})\b")

# Loose category map (start, end inclusive) → label
CATEGORIES: List[Tuple[int, int, str]] = [
    (1, 34, "3.1 System-wide"),
    (35, 46, "3.2 Public website"),
    (47, 81, "3.3 Farmer"),
    (82, 113, "3.4 Buyer"),
    (114, 138, "3.5 Driver"),
    (139, 162, "3.6 Agent"),
    (163, 197, "3.7 Admin"),
    (198, 219, "3.8 USSD"),
    (220, 244, "3.9 WhatsApp bot"),
    (245, 287, "3.10 Notifications"),
    (288, 305, "3.11 Escrow & payment"),
    (306, 320, "3.12 Academy"),
    (321, 328, "3.13 Driver tiers"),
    (329, 336, "3.14 Logistics"),
    (337, 348, "3.15 Loans"),
]


def iter_files() -> Iterable[Path]:
    for top in SCAN_DIRS:
        root = REPO_ROOT / top
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in SCAN_EXTS:
                continue
            if any(part in EXCLUDE_PARTS for part in path.parts):
                continue
            yield path


def scan() -> Dict[int, List[str]]:
    """Return {spec_id: [relative paths it appears in]}."""
    hits: Dict[int, Set[str]] = defaultdict(set)
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in MARKER_RE.finditer(text):
            spec_id = int(m.group(1))
            if 1 <= spec_id <= 348:
                rel = path.relative_to(REPO_ROOT).as_posix()
                hits[spec_id].add(rel)
    return {k: sorted(v) for k, v in hits.items()}


def category_of(spec_id: int) -> str:
    for lo, hi, label in CATEGORIES:
        if lo <= spec_id <= hi:
            return label
    return "(unknown)"


def render_summary(hits: Dict[int, List[str]]) -> str:
    covered = len(hits)
    total = len(SPEC_FUNCTIONS)
    pct = covered * 100.0 / total
    lines = [
        f"Spec coverage: {covered}/{total} ({pct:.1f}%) functions have at least one source marker",
        "Source files scanned: " + ", ".join(SCAN_DIRS),
    ]
    return "\n".join(lines)


def render_by_category(hits: Dict[int, List[str]]) -> str:
    lines = [f"{'Category':<30} {'Covered':>10} {'Total':>6} {'%':>6}"]
    lines.append("-" * 56)
    for lo, hi, label in CATEGORIES:
        ids = list(range(lo, hi + 1))
        covered = sum(1 for i in ids if i in hits)
        total = len(ids)
        pct = covered * 100.0 / total if total else 0.0
        lines.append(f"{label:<30} {covered:>10} {total:>6} {pct:>5.1f}%")
    return "\n".join(lines)


def render_missing(hits: Dict[int, List[str]]) -> str:
    missing = [i for i in SPEC_FUNCTIONS if i not in hits]
    if not missing:
        return "All 348 spec functions have at least one source marker."
    by_cat: Dict[str, List[int]] = defaultdict(list)
    for i in missing:
        by_cat[category_of(i)].append(i)
    lines = [f"Missing F#NNN markers ({len(missing)} of 348):"]
    for cat in sorted(by_cat):
        ids = by_cat[cat]
        lines.append(f"\n  {cat}  ({len(ids)})")
        # Compress runs.
        ids.sort()
        run_start = ids[0]
        prev = ids[0]
        runs: List[str] = []
        for i in ids[1:]:
            if i == prev + 1:
                prev = i
                continue
            runs.append(f"{run_start}" if run_start == prev else f"{run_start}-{prev}")
            run_start = i
            prev = i
        runs.append(f"{run_start}" if run_start == prev else f"{run_start}-{prev}")
        lines.append("    " + ", ".join(runs))
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--missing", action="store_true", help="list IDs without a marker")
    p.add_argument("--by-category", action="store_true", help="tabular per-category coverage")
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    p.add_argument("--fail-under", type=float, default=None,
                   help="exit non-zero if coverage %% is below this value")
    args = p.parse_args(argv)

    hits = scan()
    covered = len(hits)
    pct = covered * 100.0 / len(SPEC_FUNCTIONS)

    if args.json:
        out = {
            "covered": covered,
            "total": len(SPEC_FUNCTIONS),
            "percent": round(pct, 2),
            "hits": hits,
            "missing": [i for i in SPEC_FUNCTIONS if i not in hits],
        }
        print(json.dumps(out, indent=2))
    else:
        print(render_summary(hits))
        if args.by_category:
            print()
            print(render_by_category(hits))
        if args.missing:
            print()
            print(render_missing(hits))

    if args.fail_under is not None and pct < args.fail_under:
        print(f"\n❌ coverage {pct:.1f}% is below threshold {args.fail_under:.1f}%", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

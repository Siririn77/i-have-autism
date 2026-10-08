#!/usr/bin/env python3
"""Scores a pair of arms (control, treated) on the maintainability axes.

Mechanical, not impressionistic: each check is a countable fact about the file.
Run from the repo root:  python3 evals/score_quality.py <dir-with-outputs>
"""
import sys, os, re, json, subprocess

def read(p):
    try:
        with open(p, encoding='utf-8') as f:
            return f.read()
    except OSError:
        return None

def count(src, pattern):
    return len(re.findall(pattern, src or '', re.M))

# --- mechanical checks, each returns a number (higher is better unless noted) ---

def check_one_place(src):
    """DRY: count values that appear as both a literal and a repeated constant."""
    # a numeric literal repeated 2+ times that is not 0/1/-1
    nums = re.findall(r'\b(\d{2,})\b', src or '')
    repeated = sum(1 for n in set(nums) if nums.count(n) > 1)
    return -repeated  # negative: fewer repeats is better

def check_contract(src):
    """Count exported functions that carry a JSDoc/contract block."""
    blocks = count(src, r'/\*\*')
    exports = count(src, r'\bmodule\.exports\b|\bexport\s+(?:default\s+)?(?:function|class|const)')
    return 1 if blocks > 0 else 0

def check_loud_failure(src):
    """Explicit guards / throws vs silent returns of sentinel."""
    throws = count(src, r'\bthrow\b')
    guards = count(src, r'\bif\s*\([^)]*\)\s*(?:return\s*\[\]|return\s*null|return\s*undefined|throw)')
    return throws + guards

def check_verifiable(src):
    """Presence of any assert/test/invariant in the same file or a sibling test."""
    return 1 if re.search(r'\bassert|expect\(|\btest\(|it\(|=== true|!== ', src or '') else 0

def check_no_implicit(src):
    """Comments that name a deliberate decision (vs comments that restate code)."""
    return count(src, r'//.*(?:deliberate|intentionally|on purpose|by design|note:|why:)')

def check_readable_names(src):
    """Short/opaque identifiers: single letters outside loop index i/j/k."""
    names = re.findall(r'\b([a-hl-z])\b', src or '')
    return -len(names)

def metrics(path):
    src = read(path)
    if src is None:
        return None
    lines = src.count('\n') + 1
    return {
        'bytes': len(src.encode('utf-8')),
        'lines': lines,
        'score': {
            'one_place_to_change': check_one_place(src),
            'contract_present': check_contract(src),
            'loud_failure': check_loud_failure(src),
            'verifiable': check_verifiable(src),
            'nothing_implicit': check_no_implicit(src),
            'readable_names': check_readable_names(src),
        },
        # negative-value checks are reported as-is; the reader sums them with sign
        'maintainability_total': (
            check_one_place(src) + check_contract(src) + check_loud_failure(src)
            + check_verifiable(src) + check_no_implicit(src) + check_readable_names(src)
        ),
    }

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    out = {}
    for task in ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']:
        row = {}
        for arm in ['control', 'treated']:
            for ext in ('js', 'md'):
                p = os.path.join(d, f'{task}_{arm}.{ext}')
                if os.path.exists(p):
                    row.setdefault(arm, {})[ext] = metrics(p)
        if row:
            out[task] = row
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()

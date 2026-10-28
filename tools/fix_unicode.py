#!/usr/bin/env python3
"""Rewrite non-ASCII characters in bundles as \\uXXXX escapes.

Usage: python3 tools/fix_unicode.py [--check] BUNDLE ...

Each BUNDLE is a path to a .properties file, or a bundle name such as projectx_fr (looked up in
the bundle directory next to this tools directory). Files are read as UTF-8; a file that isn't
valid UTF-8 is read as Windows-1252, the usual encoding of editors that don't save UTF-8.
Characters outside the Basic Multilingual Plane are written as UTF-16 surrogate pairs, the way
java.util.Properties expects them. A leading byte order mark is removed. Line endings are kept.

With --check, nothing is written; files that need fixing are listed and the exit status is 1.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve(name):
    """The path for a bundle argument: an existing path, or a bundle name in the bundle directory."""
    if os.path.isfile(name):
        return name
    base = name if name.endswith(".properties") else name + ".properties"
    path = os.path.join(ROOT, base)
    if os.path.isfile(path):
        return path
    sys.exit(f"no such bundle: {name}")


def escape(c):
    code = ord(c)
    if code > 0xFFFF:
        code -= 0x10000
        return f"\\u{0xD800 + (code >> 10):04x}\\u{0xDC00 + (code & 0x3FF):04x}"
    return f"\\u{code:04x}"


def fix(path, check):
    """Escape the non-ASCII characters in one file; return how many lines changed."""
    with open(path, "rb") as f:
        data = f.read()
    raw = data.removeprefix(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        print(f"{path}: not valid UTF-8; read it as Windows-1252, check the result")
    lines = text.splitlines(keepends=True)
    fixed = ["".join(escape(c) if ord(c) > 127 else c for c in line) for line in lines]
    changed = [n for n, (a, b) in enumerate(zip(lines, fixed), 1) if a != b]
    out = "".join(fixed).encode("ascii")
    if out == data:
        return 0
    if check:
        print(f"{path}: needs fixing on line(s) {', '.join(map(str, changed)) or '1 (byte order mark)'}")
    else:
        with open(path, "wb") as f:
            f.write(out)
        print(f"{path}: escaped non-ASCII characters on {len(changed)} line(s)")
    return max(len(changed), 1)


def main():
    ap = argparse.ArgumentParser(description="Rewrite non-ASCII characters in bundles as \\uXXXX escapes.")
    ap.add_argument("--check", action="store_true", help="only report files that need fixing")
    ap.add_argument("bundles", nargs="+", help="bundle files or names (e.g. projectx_fr)")
    args = ap.parse_args()
    paths = [resolve(b) for b in args.bundles]
    changed = sum(1 for p in paths if fix(p, args.check))
    if not changed:
        print("nothing to fix")
    sys.exit(1 if args.check and changed else 0)


if __name__ == "__main__":
    main()

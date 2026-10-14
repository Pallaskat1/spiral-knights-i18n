#!/usr/bin/env python3
"""Sanity-check the translation bundles against the default English bundles.

Usage: python3 tools/check_bundles.py [--lang LANG ...] [--bundle NAME ...] [bundle_dir]

With --lang (e.g. --lang es), only problems in that language's bundles are reported.
With --bundle (e.g. --bundle pvp), only problems in that bundle (English and translations) are reported.
Both together report only the files matching both.

Errors (exit status 1):
  - a translation key that the English bundle doesn't have, or a bundle with no English bundle
  - characters above 127 that are not written as \\uXXXX escapes
  - duplicate keys in one file
  - {0}-style placeholders, HTML tags or "|" separators that differ from the English
  - an escaped backslash before "n" (shows up in game as a literal "\\n")
  - a chat command alias (c.* keys) used by more than one command in the same language

Warnings:
  - a different number of line breaks (\\n) than the English
  - leading spaces that differ from the English
  - a translation identical to the English (redundant: English is the fallback)
  - Portuguese text that looks Spanish (heuristic)
"""
import argparse
import os
import re
import sys

LANG_SUFFIX = re.compile(r"^(?P<base>.+?)_(?P<lang>[a-z]{2}(?:_[A-Z]{2})?)\.properties$")
PLACEHOLDER = re.compile(r"\{\d+(?:,[^{}]*)?\}")
TAG = re.compile(r"</?(?:html|body|font|center|div|span|img|table|tr|td|th|ul|ol|li|h[1-6]|strong|em|"
                 r"sup|sub|hr|tt|small|big|pre|code|br|b|i|u|p|a)(?:\s+[a-zA-Z-]+\s*=[^<>]*)?\s*/?>", re.I)
NEWLINE = re.compile(r"(?<!\\)(?:\\\\)*\\n")
ESCAPED_BACKSLASH_N = re.compile(r"(?<!\\)(?:\\\\)+n")
SPANISH = re.compile(r"[ñ¿¡]|\b(?:y|el|los|las|del|una|usted|puedes|tienes|muy|pero|hay|aquí|también|"
                     r"caballero|caballeros|hasta|donde|siempre|cuando|después|ningún|algún)\b|\w(?:ción|ciones)\b",
                     re.I)


class Prop:
    def __init__(self, key, raw, line):
        self.key, self.raw, self.line = key, raw, line


def _is_ws(c):
    return c in " \t\f"


def _continues(s):
    return (len(s) - len(s.rstrip("\\"))) % 2 == 1


def decode(s):
    """Decode escapes the way java.util.Properties does."""
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            d = s[i + 1]
            if d == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", s[i + 2:i + 6]):
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
                continue
            out.append({"t": "\t", "n": "\n", "r": "\r", "f": "\f"}.get(d, d))
            i += 2
            continue
        if c != "\\":
            out.append(c)
        i += 1
    return "".join(out)


def parse(path):
    """Return (props, problems) for one file, following Properties.load() line rules."""
    with open(path, "rb") as f:
        data = f.read()
    problems = []
    for n, line in enumerate(data.split(b"\n"), 1):
        if any(b > 127 for b in line):
            problems.append((n, "error", "non-ASCII character; write it as a \\uXXXX escape"))
    lines = re.split(r"\r\n|\r|\n", data.decode("latin-1"))
    props, i = [], 0
    while i < len(lines):
        text = lines[i].lstrip(" \t\f")
        if not text or text[0] in "#!":
            i += 1
            continue
        start = i
        while _continues(text) and i + 1 < len(lines):
            i += 1
            text = text[:-1] + lines[i].lstrip(" \t\f")
        k = 0
        while k < len(text) and not (text[k] in "=:" or _is_ws(text[k])):
            k += 2 if text[k] == "\\" else 1
        v = k
        while v < len(text) and _is_ws(text[v]):
            v += 1
        if v < len(text) and text[v] in "=:":
            v += 1
            while v < len(text) and _is_ws(text[v]):
                v += 1
        props.append(Prop(decode(text[:k]), text[v:], start + 1))
        i += 1
    return props, problems


def compare(lang, en, tr):
    """Problems with one translated value compared to its English source."""
    out = []
    e, t = decode(en.raw), decode(tr.raw)
    if sorted(PLACEHOLDER.findall(e)) != sorted(PLACEHOLDER.findall(t)):
        out.append(("error", "placeholders differ from English"))
    if sorted(x.lower() for x in TAG.findall(e)) != sorted(x.lower() for x in TAG.findall(t)):
        out.append(("error", "HTML tags differ from English"))
    if e.count("|") != t.count("|"):
        out.append(("error", "number of '|' separators differs from English"))
    if ESCAPED_BACKSLASH_N.search(tr.raw) and not ESCAPED_BACKSLASH_N.search(en.raw):
        out.append(("error", "escaped backslash before n (shows a literal \\n); use \\n"))
    if len(NEWLINE.findall(tr.raw)) != len(NEWLINE.findall(en.raw)):
        out.append(("warning", "number of line breaks (\\n) differs from English"))
    if len(e) - len(e.lstrip(" ")) != len(t) - len(t.lstrip(" ")):
        out.append(("warning", "leading spaces differ from English"))
    if e == t:
        out.append(("warning", "identical to English (redundant; English is the fallback)"))
    if lang.startswith("pt") and len(set(m.group(0).lower() for m in SPANISH.finditer(t))) >= 2:
        out.append(("warning", "looks like Spanish"))
    return out


def wanted(name, langs, bundles):
    """Whether problems in this file should be reported for the requested languages and bundles."""
    m = LANG_SUFFIX.match(name)
    if bundles and (m.group("base") if m else name[:-len(".properties")]) not in bundles:
        return False
    if not langs:
        return True
    return bool(m) and any(m.group("lang") == l or m.group("lang").startswith(l + "_") for l in langs)


def main():
    ap = argparse.ArgumentParser(description="Sanity-check the translation bundles against the English bundles.")
    ap.add_argument("--lang", action="append", default=[],
                    help="only report problems in this language's bundles (e.g. es); may be repeated")
    ap.add_argument("--bundle", action="append", default=[],
                    help="only report problems in this bundle and its translations (e.g. pvp); may be repeated")
    ap.add_argument("bundle_dir", nargs="?",
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    args = ap.parse_args()
    root = args.bundle_dir
    names = sorted(n for n in os.listdir(root) if n.endswith(".properties"))
    checked = [n for n in names if wanted(n, args.lang, args.bundle)]
    if not checked:
        what = []
        if args.lang:
            what.append(f"language(s) {', '.join(args.lang)}")
        if args.bundle:
            what.append(f"bundle(s) {', '.join(args.bundle)}")
        print(f"no bundles found for {' and '.join(what)}")
        sys.exit(1)
    parsed = {n: parse(os.path.join(root, n)) for n in names}
    report = []  # (file, line, level, message)
    for name, (props, problems) in parsed.items():
        report += [(name, line, level, msg) for line, level, msg in problems]
        seen = {}
        for p in props:
            if p.key in seen:
                report.append((name, p.line, "error", f"duplicate key {p.key} (first on line {seen[p.key]})"))
            seen.setdefault(p.key, p.line)
    for name in names:
        m = LANG_SUFFIX.match(name)
        if not m:
            continue
        base, lang = m.group("base"), m.group("lang")
        en_name = base + ".properties"
        if en_name not in parsed:
            report.append((name, 1, "error", f"no English bundle {en_name}"))
            continue
        en = {p.key: p for p in parsed[en_name][0]}
        for p in parsed[name][0]:
            if p.key not in en:
                report.append((name, p.line, "error", f"{p.key} is not in {en_name}"))
                continue
            for level, msg in compare(lang, en[p.key], p):
                report.append((name, p.line, level, f"{p.key}: {msg}"))
    # Chat commands a player can type in each language: the translated aliases, or the English
    # ones for commands the translation leaves out.
    en_chat = [p for p in parsed.get("chat.properties", ([], []))[0] if p.key.startswith("c.")]
    for name in names:
        m = LANG_SUFFIX.match(name)
        if not m or m.group("base") != "chat":
            continue
        translated = {p.key: p for p in parsed[name][0]}
        owners = {}
        for p in en_chat:
            for alias in decode(translated.get(p.key, p).raw).lower().split():
                owners.setdefault(alias, set()).add(p.key)
        for alias, keys in sorted(owners.items()):
            if len(keys) > 1:
                report.append((name, 1, "error", f"chat alias '{alias}' is used by {', '.join(sorted(keys))}"))
    report = [r for r in report if wanted(r[0], args.lang, args.bundle)]
    for name, line, level, msg in sorted(report):
        print(f"{name}:{line}: {level}: {msg}")
    errors = sum(1 for r in report if r[2] == "error")
    warnings = len(report) - errors
    print(f"{errors} error(s), {warnings} warning(s) in {len(checked)} files")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

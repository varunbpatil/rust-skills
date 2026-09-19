#!/usr/bin/env python3
"""Structural / link / index validation for the rule library.

Checks (no Rust toolchain needed):
  - every rules/<id>.md starts with `# <id>` matching its filename
  - has a `> ` one-line summary near the top
  - has `## Why It Matters` and `## See Also`
  - has explicit `## Bad` and `## Good` contrast sections
  - summaries, Rust examples, and See Also targets are not duplicated
  - Rust fences do not hide all Rust syntax behind ordinary comments
  - every local Markdown link resolves, including links outside rules/
  - every rule has at least two non-self cross-rule references
  - SKILL.md links exactly the set of files in rules/ (no broken links, no orphans)

Exits non-zero (and prints every problem) if anything fails.
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RULES = ROOT / "rules"
SKILL = ROOT / "SKILL.md"
COVERAGE = ROOT / "SOURCE_COVERAGE.md"

errors = []


def err(msg):
    errors.append(msg)


rule_files = sorted(RULES.glob("*.md"))
rule_names = {p.name for p in rule_files}
summaries = {}
rust_blocks = {}

link_re = re.compile(r"\]\(([^)]+)\)")
commented_rust_re = re.compile(
    r"^(?:"
    r"#\[|use\b|extern\s+crate\b|let\b|"
    r"(?:(?:pub(?:\([^)]*\))?\s+)?(?:async\s+|unsafe\s+)?"
    r"(?:fn|struct|enum|union|trait|impl|type|const|static|mod)\b)|"
    r"[A-Za-z_]\w*(?:(?:::|\.)[A-Za-z_]\w*)*\s*(?:[!(]|=)"
    r")"
)


def is_only_commented_out_rust(body):
    """Return true when a Rust fence hides all of its code behind comments."""
    without_block_comments = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
    executable = "\n".join(
        line
        for line in without_block_comments.splitlines()
        if not line.lstrip().startswith("//")
    )
    if executable.strip():
        return False

    payloads = []
    for line in body.splitlines():
        # `///` and `//!` fences intentionally demonstrate documentation.
        match = re.match(r"^\s*//(?![/!])\s?(.*)$", line)
        if match:
            payloads.append(match.group(1).strip())
    for block in re.findall(r"/\*(.*?)\*/", body, flags=re.DOTALL):
        payloads.extend(line.strip().lstrip("*").strip() for line in block.splitlines())

    return any(commented_rust_re.match(line) for line in payloads if line)


for p in rule_files:
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    head = lines[0].strip() if lines else ""
    if head != f"# {p.stem}":
        err(f"{p.name}: first line is {head!r}, expected '# {p.stem}'")
    summary = next((l[2:].strip() for l in lines[:6] if l.startswith("> ")), None)
    if summary is None:
        err(f"{p.name}: missing '> ' summary line near the top")
    else:
        normalized = " ".join(summary.lower().split())
        if normalized in summaries:
            err(f"{p.name}: duplicates summary from {summaries[normalized]}")
        summaries[normalized] = p.name
    for section in ("## Why It Matters", "## Bad", "## Good", "## See Also"):
        if section not in text:
            err(f"{p.name}: missing '{section}' section")
    for section in ("Bad", "Good"):
        marker = f"## {section}\n"
        if marker in text:
            body = text.split(marker, 1)[1].split("\n## ", 1)[0]
            if "```" not in body:
                err(f"{p.name}: '{marker.strip()}' section has no fenced example")
    # Match fences of any length (three or more backticks), including the
    # longer fences needed when a Rust example contains nested Markdown.
    for fence in re.finditer(
        r"(?P<open>`{3,})([^\n]*)\n(.*?)\n(?P<close>(?P=open)`*)\s*(?:\n|$)",
        text,
        flags=re.DOTALL,
    ):
        _, info, body, _ = fence.groups()
        if info.strip().split(",", 1)[0] != "rust":
            continue
        if is_only_commented_out_rust(body):
            line = text.count("\n", 0, fence.start()) + 1
            err(
                f"{p.name}:{line}: Rust fence contains only commented-out code; "
                "make it executable or use a non-Rust fence"
            )
        normalized = "\n".join(line.rstrip() for line in body.strip().splitlines())
        if len(normalized) < 40:
            continue
        previous = rust_blocks.get(normalized)
        if previous is not None and previous != p.name:
            err(f"{p.name}: duplicates a Rust example from {previous}")
        rust_blocks[normalized] = p.name
    see_also = text.split("## See Also", 1)[1] if "## See Also" in text else ""
    related = []
    for raw in link_re.findall(see_also):
        target = raw.split("#", 1)[0]
        target = target.removeprefix("./")
        if target.endswith(".md"):
            related.append(pathlib.PurePosixPath(target).name)
    if p.name in related:
        err(f"{p.name}: See Also contains a self-link")
    if len(related) != len(set(related)):
        err(f"{p.name}: See Also contains a duplicate rule link")
    if len(set(related)) < 2:
        err(f"{p.name}: See Also must contain at least two distinct rule links")

# Validate every repository-local Markdown target, not only the simple rule
# links that happen to match the index naming convention.
markdown_files = (
    list(ROOT.glob("*.md"))
    + list(RULES.glob("*.md"))
    + list((ROOT / "checks").glob("*.md"))
)
for source in markdown_files:
    text = source.read_text(encoding="utf-8")
    prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for raw in link_re.findall(prose):
        if raw.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = raw.split("#", 1)[0]
        if not target or not target.endswith(".md"):
            continue
        resolved = (source.parent / target).resolve()
        if not resolved.is_file():
            err(f"{source.relative_to(ROOT)}: broken local link -> {raw}")

# Retain one manifest entry for every requested Corrode article (including the
# deliberate exclusion) and the HowToCodeIt guide.
expected_corrode = {
    "dyn-compatibility",
    "hardening-rust",
    "ugly",
    "bugs-rust-wont-catch",
    "defensive-programming",
    "simple",
    "sharp-edges-in-rust-std",
    "pitfalls-of-safe-rust",
    "expressions",
    "prototyping",
    "rust-option-handling-best-practices",
    "lifetimes",
    "iterators",
    "idiomatic-rust-resources",
    "paradigms",
    "immutability",
    "compile-time-invariants",
    "enums",
    "illegal-state",
    "dont-use-preludes-and-globs",
}
if not COVERAGE.is_file():
    err("SOURCE_COVERAGE.md: missing supplemental-source manifest")
else:
    coverage = COVERAGE.read_text(encoding="utf-8")
    found_corrode = set(re.findall(r"https://corrode\.dev/blog/([^/)]+)/", coverage))
    for slug in sorted(expected_corrode - found_corrode):
        err(f"SOURCE_COVERAGE.md: missing Corrode article {slug}")
    if (
        "https://www.howtocodeit.com/guides/master-hexagonal-architecture-in-rust"
        not in coverage
    ):
        err("SOURCE_COVERAGE.md: missing HowToCodeIt hexagonal-architecture guide")

# SKILL.md index parity
skill = SKILL.read_text(encoding="utf-8")
linked = set(re.findall(r"rules/([a-z0-9-]+\.md)", skill))
for tgt in sorted(linked):
    if tgt not in rule_names:
        err(f"SKILL.md: links missing file rules/{tgt}")
for name in sorted(rule_names):
    if name not in linked:
        err(f"SKILL.md: rule rules/{name} is not listed in the index")

if errors:
    print(f"VALIDATION FAILED ({len(errors)} problem(s)):\n")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print(f"OK: {len(rule_files)} rules valid; index lists all {len(linked)} of them.")

# checks — compile-verify the rule examples

A dev tool that type-checks the ` ```rust ` code blocks in `../rules/*.md` so the
"Good" examples we tell agents to write actually compile. Not part of the
published skill.

## Run

```bash
# structural / link / index checks (no toolchain needed)
python3 checks/validate.py

# compile-check the examples
cd checks
python3 gen.py                                              # extract blocks -> examples/
cargo check --examples --keep-going --message-format=json > check.json
python3 analyze.py check.json                               # classify results
python3 analyze.py check.json --check-quality quality-baseline.json
python3 analyze.py check.json --check-baseline baseline.txt # CI gate: fail on NEW suspects
```

Both run in CI (`.github/workflows/ci.yml`): `validate` (Python only) and
`examples` (pinned to Rust 1.98.1, the toolchain `baseline.txt` was generated on).

## Updating the baseline

`baseline.txt` lists any explicitly accepted suspects; it is currently empty.
`quality-baseline.json` is a second, directional ratchet: Rust blocks, checked
examples, and clean examples may not decrease, while explicitly ignored blocks,
fragments, extraction artifacts, low-signal failures, and suspects may not
increase. Improve its numbers whenever examples are made self-contained. After
an intentional change, regenerate the relevant file on the pinned toolchain and
review the diff:

```bash
rustup run 1.98.1 cargo check --examples --keep-going --message-format=json > check.json
python3 analyze.py check.json --emit-baseline > baseline.txt
python3 analyze.py check.json --emit-quality > quality-baseline.json
```

When bumping the pinned toolchain in `ci.yml`, regenerate `baseline.txt` on the
same version in the same commit.

## How it works

`gen.py` extracts each candidate block into `examples/<name>.rs`, wrapping
fragments in an `async fn -> Result<...>` so `?` and `.await` type-check. It
skips blocks that can't compile standalone by design: `## Bad` anti-patterns,
nightly `#![feature]` gates, procedural-macro code, placeholder crate names
(`my_crate`, …), and bare `...` pseudocode. It compiles `rust,no_run` blocks
but ignores Rust fences nested inside longer Markdown demonstration fences.

`validate.py` also enforces explicit `Bad`/`Good` sections, rejects repeated
rule summaries, repeated Rust example blocks, Rust fences that hide all Rust
syntax behind ordinary comments, self-links, and duplicate `See Also` targets,
and checks the article-by-article supplemental-source manifest in
`SOURCE_COVERAGE.md`. Documentation-comment demonstrations (`///` and `//!`)
remain valid; use a non-Rust fence for explanatory comments that are not meant
to compile.

`analyze.py` buckets each failing example by compiler error code:

- **fragment** — every error is name resolution (undefined domain symbol/crate). These
  reference helpers defined elsewhere in the rule; expected, ignored.
- **artifact** — caused by extraction (a `&self` method body wrapped as a free
  fn, pseudocode `...`/`???` tokens, dangling doc comments). Not real bugs.
- **low** — only "type annotations needed"; compiles in the rule's real context.
- **SUSPECT** — anything else (type mismatch, no-method, bad syntax, wrong
  arity, missing trait impl, unknown field, unstable API). These are the ones to
  review and fix. In particular, E0561 and E0658 are never treated as fragments.

## Notes

- Run on the pinned Rust 1.98.1 toolchain; examples intentionally target the
  repository's documented current stable version.
- Generated files (`examples/`, `check*.json`, `manifest.json`,
  `generation-stats.json`, `target/`) are gitignored. The directional quality
  baseline is tracked so CI can enforce the current floor and ceilings.

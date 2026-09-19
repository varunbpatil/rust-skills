# unsafe-miri-ci

> Run `cargo miri test` in CI for every crate that contains `unsafe` code.

## Why It Matters

Miri is an interpreter designed to detect many classes of undefined behavior in
executed Rust code. It catches out-of-bounds memory accesses, use-after-free,
reads of uninitialized memory, invalid pointer use, some data races, and
violations of its selected aliasing model. It complements rather than replaces
code review, sanitizers, platform testing, or concurrency model checkers.

Static analysis and code review can miss subtle UB. Miri checks only paths that
the test suite executes, so focused tests around unsafe abstractions are vital.

## Bad

```yaml
# CI that tests but never runs Miri — unsafe code ships unverified.
- name: Test
  run: cargo test --all-features
```

## Good

```yaml
# .github/workflows/miri.yml
name: Miri

on: [push, pull_request]

jobs:
  miri:
    name: Miri (nightly)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install nightly toolchain with Miri
        run: |
          rustup toolchain install nightly --component miri
          rustup override set nightly
          cargo miri setup

      - name: Run Miri
        env:
          MIRIFLAGS: "-Zmiri-strict-provenance"
        run: cargo miri test --all-features
```

## Key Points

- **Nightly only**: Miri requires a nightly toolchain. Pin a specific nightly date in `rust-toolchain.toml` if you need reproducible CI.
- **Slow**: Miri interprets rather than compiling to native code, so suites can
  run orders of magnitude slower. Measure the project, then use a focused test
  set or a separate CI job if the full suite is prohibitive.
- **`MIRIFLAGS`**: `-Zmiri-strict-provenance` enables stricter pointer provenance checks, catching casts that violate the provenance model. Add `-Zmiri-tree-borrows` to opt into the newer Tree Borrows model.
- **Stacked Borrows**: Miri's default aliasing model. It catches violations of Rust's borrow rules at the pointer level — invaluable for raw-pointer and FFI code.
- **Setup command**: `cargo miri setup` pre-builds the Miri sysroot so the first test run is not cold. Run it once per CI cache key.
- Prioritize crates that contain unsafe abstractions. Safe callers can still
  provide valuable coverage of unsafe dependencies exercised through safe APIs.

## When It's Acceptable to Skip

- Safe-only crates whose Miri-compatible tests do not exercise relevant unsafe
  dependencies, once higher-risk crates have coverage.
- Generated code or proc-macro output you do not control (audit the generator instead).
- Very large integration tests that make Miri impractical — run a targeted unit-test subset instead.

## See Also

- [unsafe-maybeuninit](unsafe-maybeuninit.md) - use `MaybeUninit<T>` for uninitialized memory
- [unsafe-safety-comment](unsafe-safety-comment.md) - document every unsafe block
- [test-criterion-bench](test-criterion-bench.md) - use criterion for benchmarking (separate from Miri)

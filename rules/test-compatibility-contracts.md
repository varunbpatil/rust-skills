# test-compatibility-contracts

> Preserve required observable behavior with explicit compatibility and differential tests

## Why It Matters

When Rust replaces an existing tool, protocol implementation, or parser,
type-safe code can still change exit codes, accepted inputs, ordering, path
semantics, or error behavior. Those differences may break callers even when the
new behavior looks cleaner. Define which quirks are contractual, capture them
as tests, and make intentional incompatibilities explicit.

Compatibility does not require preserving a vulnerability. Security fixes take
precedence, but the changed behavior, migration path, and affected edge cases
must be deliberate rather than accidental.

## Bad

```rust
fn parse_legacy_bool(input: &str) -> Result<bool, &'static str> {
    // A rewrite that silently drops previously accepted spellings.
    match input {
        "true" => Ok(true),
        "false" => Ok(false),
        _ => Err("invalid boolean"),
    }
}
```

## Good

```rust
fn parse_legacy_bool(input: &str) -> Result<bool, &'static str> {
    match input {
        "true" | "1" | "yes" => Ok(true),
        "false" | "0" | "no" => Ok(false),
        _ => Err("invalid boolean"),
    }
}

#[test]
fn preserves_legacy_boolean_spellings() {
    for value in ["true", "1", "yes"] {
        assert_eq!(parse_legacy_bool(value), Ok(true));
    }
    for value in ["false", "0", "no"] {
        assert_eq!(parse_legacy_bool(value), Ok(false));
    }
}
```

For a real replacement, run the old and new implementations over a shared
corpus and compare structured results. Snapshot tests are useful for stable
human-facing output; property tests are useful for broad parser equivalence.

For a published library, run
[`cargo-semver-checks`](https://crates.io/crates/cargo-semver-checks) against the
intended baseline to catch many public-API semver hazards. It complements the
behavioral tests above: API compatibility does not prove equivalent runtime
behavior, and not every deliberate semver exception is automatically wrong.

## See Also

- [test-snapshot-testing](./test-snapshot-testing.md) - lock down complex observable output
- [test-proptest-properties](./test-proptest-properties.md) - explore broad input spaces
- [security-filesystem-boundaries](./security-filesystem-boundaries.md) - preserve behavior without trusting paths

## Source

Distilled from [Bugs Rust Won't Catch](https://corrode.dev/blog/bugs-rust-wont-catch/).

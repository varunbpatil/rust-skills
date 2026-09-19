# security-secret-comparisons

> Use constant-time comparison for secrets and avoid exposing them through diagnostics

## Why It Matters

Ordinary equality may stop at the first different byte, making it unsuitable for
comparing attacker-observable authentication secrets such as MACs, tokens, or
password-verifier outputs. Use a vetted constant-time comparison from a
cryptographic library for those values. Never implement cryptographic comparison
by hand, and keep secrets out of `Debug`, `Display`, errors, and tracing fields.

Normal identifiers and public values do not need constant-time comparison;
apply it only where a timing oracle could reveal secret material.

## Bad

```rust
fn token_matches(expected: &[u8], supplied: &[u8]) -> bool {
    expected == supplied // do not use for attacker-observable secrets
}
```

## Good

### Use a Vetted Primitive

```toml
# Cargo.toml — select a maintained cryptographic crate for the protocol.
[dependencies]
subtle = "2"
```

```rust
use subtle::ConstantTimeEq;

fn token_matches(expected: &[u8; 32], supplied: &[u8; 32]) -> bool {
    expected.ct_eq(supplied).into()
}
```

Use a fixed-size representation when the protocol specifies one; a separate
public length check can otherwise leak length even if content comparison is
constant-time. Wrap tokens in a type whose `Debug` implementation is redacted.
Do not replace this with a hand-written loop: constant-time behavior is easy to
get wrong.

For owned secret buffers whose lifetime in memory is part of the threat model,
use [`secrecy`](https://crates.io/crates/secrecy) to control explicit exposure
and clear supported contents on drop. For other owned secret types, derive or
implement [`zeroize::Zeroize`](https://crates.io/crates/zeroize) and
`ZeroizeOnDrop` as appropriate. Zeroization reduces retention in the owned
allocation; it cannot erase earlier copies, logged values, swap, allocator
remnants, or representations held by another process. Avoid creating those
copies in the first place.

## See Also

- [obs-no-sensitive-data](./obs-no-sensitive-data.md) - redact diagnostics and logs
- [type-newtype-validated](./type-newtype-validated.md) - use types to protect sensitive values
- [security-dependency-audit](./security-dependency-audit.md) - use reviewed dependencies

## Source

Distilled from [Pitfalls of Safe Rust](https://corrode.dev/blog/pitfalls-of-safe-rust/).

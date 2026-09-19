# security-panic-semantics

> Choose, test, and document panic behavior at production trust boundaries

## Why It Matters

Panics are not recoverable application errors. Depending on the profile and
execution context they unwind a task or thread, or abort the whole process;
stack overflow and allocation failure may abort regardless. A panic hook adds
diagnostics but does not make a panic safe to recover from.

Return `Result` for malformed or untrusted input. Reserve panics for broken
internal invariants, document public panic conditions, and test the release
binary's behavior rather than assuming debug behavior applies in production.

## Bad

```rust
fn parse_port(input: &str) -> u16 {
    input.parse().unwrap() // malformed external input can terminate work
}
```

## Good

### Separate Input Errors from Invariants

```rust
fn parse_port(input: &str) -> Result<u16, &'static str> {
    input.parse().map_err(|_| "port must be an unsigned 16-bit integer")
}

fn first_byte(bytes: &[u8]) -> u8 {
    *bytes.first().expect("caller maintains the non-empty invariant")
}
```

The first function can receive hostile input and returns `Result`. The second
is only appropriate when its caller has already established and owns the stated
invariant; expose a fallible API instead when that is not true.

### Prefer Checked Boundary APIs

```rust
fn split_payload(payload: &[u8], header_len: usize) -> Result<(&[u8], &[u8]), &'static str> {
    payload
        .split_at_checked(header_len)
        .ok_or("header length exceeds payload length")
}
```

The panicking `split_at` is appropriate only after the caller has established
the index invariant. For untrusted lengths, the checked variant keeps malformed
input in the typed error path.

## See Also

- [err-result-over-panic](./err-result-over-panic.md) - use recoverable errors
- [err-no-unwrap-prod](./err-no-unwrap-prod.md) - avoid unchecked failure paths
- [doc-panics-section](./doc-panics-section.md) - document public panics
- [perf-release-profile](./perf-release-profile.md) - configure release panic strategy

## Source

Distilled from [Hardening Rust Code For Production](https://corrode.dev/blog/hardening-rust/)
and [Pitfalls of Safe Rust](https://corrode.dev/blog/pitfalls-of-safe-rust/).

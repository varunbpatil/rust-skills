# security-filesystem-boundaries

> Treat filesystem paths and metadata as untrusted, time-varying boundary inputs

## Why It Matters

Checking a path and then opening it is vulnerable to time-of-check/time-of-use
races: another process can replace a symlink or file between operations. String
paths also do not reliably identify a file, and Unix filenames need not be UTF-8.

Use handles or platform-aware APIs that combine validation with the operation
when security depends on it. Set restrictive permissions at file creation time,
not in a later `chmod`; validate path components against traversal; and avoid
converting OS paths to `str` unless the boundary requires UTF-8.

## Bad

```rust
fn unsafe_child(root: &std::path::Path, input: &std::path::Path) -> std::path::PathBuf {
    root.join(input) // an absolute input discards `root`; `..` can escape it
}
```

## Good

### Validate Components Before Joining

`Path::join` replaces the left side when its right side is absolute. Validate a
user-supplied relative path before joining it to a trusted root.

```rust
use std::path::{Component, Path, PathBuf};

fn safe_child(root: &Path, input: &Path) -> Result<PathBuf, &'static str> {
    if input.is_absolute() || input.components().any(|component| {
        matches!(component, Component::ParentDir | Component::RootDir | Component::Prefix(_))
    }) {
        return Err("path must be a relative child");
    }
    Ok(root.join(input))
}
```

This validation does not eliminate symlink races. When the operation is
security-sensitive, use a handle-relative, platform-aware API that resolves and
opens within the trusted directory in one operation. Create private files with
their final restrictive mode; a later permission change leaves a race window.

## Ecosystem Choices

[`cap-std`](https://crates.io/crates/cap-std) provides capability-oriented,
directory-handle-relative filesystem APIs. It is a useful foundation when a
component should operate only beneath directories explicitly supplied to it;
review its symlink and platform semantics for the exact operation being
protected. [`camino`](https://crates.io/crates/camino) provides UTF-8 path types
when UTF-8 is an intentional application boundary. It does not make paths safe
or eliminate traversal and race concerns.

## See Also

- [err-result-over-panic](./err-result-over-panic.md) - surface recoverable boundary failures
- [type-newtype-validated](./type-newtype-validated.md) - validate data at construction
- [unsafe-minimize-scope](./unsafe-minimize-scope.md) - isolate platform-specific unsafe code
- [security-resource-limits](./security-resource-limits.md) - bound untrusted boundary work

## Source

Distilled from [Bugs Rust Won't Catch](https://corrode.dev/blog/bugs-rust-wont-catch/) and [Pitfalls of Safe Rust](https://corrode.dev/blog/pitfalls-of-safe-rust/).

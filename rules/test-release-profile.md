# test-release-profile

> Test production-relevant behavior under the release configuration you ship

## Why It Matters

Debug and release builds can differ in overflow checking, debug assertions,
panic strategy, optimization-sensitive behavior, enabled features, and linked
native code. A debug-only test pass does not establish that the production
artifact behaves correctly. Keep ordinary debug tests for fast feedback, then
add release-profile tests for behavior that can differ.

`cargo test --release` tests with Cargo's release profile; it does not replace a
smoke test of the exact packaged binary, container, target CPU baseline, feature
set, environment, and deployment configuration that will ship.

## Bad

```bash
# The only CI validation:
cargo test
```

## Good

```bash
set -euo pipefail

cargo test --locked --all-features
cargo test --locked --all-features --release
cargo build --locked --release
./scripts/smoke-test-artifact target/release/my-service
```

Select features and targets that match supported production combinations;
`--all-features` is not representative when features are mutually exclusive.
Tests must assert intended overflow and panic behavior rather than depending on
profile defaults accidentally.

## See Also

- [security-panic-semantics](./security-panic-semantics.md) - choose boundary panic behavior
- [perf-release-profile](./perf-release-profile.md) - configure release trade-offs deliberately
- [test-integration-dir](./test-integration-dir.md) - exercise public behavior from integration tests

## Source

Distilled from [Hardening Rust Code For Production](https://corrode.dev/blog/hardening-rust/).

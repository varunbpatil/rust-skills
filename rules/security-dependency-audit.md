# security-dependency-audit

> Audit dependency advisories, licenses, and duplicate versions in CI

## Why It Matters

Cargo resolves and compiles dependency code safely, but it cannot establish that
the selected versions have no published vulnerabilities or unacceptable license
and source-policy risks. Check the complete dependency graph in CI and make
exceptions explicit, reviewed, and time-limited.

`cargo audit` checks RustSec advisories. `cargo deny` enforces license, source,
and duplicate-version policy; its available checks vary by tool version, so pin
the CI tool and configuration. Keep advisory database update behavior
reproducible as well.

Unsafe-code inventory is a separate signal. A tool such as `cargo geiger` can
show where the resolved graph contains `unsafe`, but the count is neither a
vulnerability report nor proof that an unsafe-free dependency is correct.
Review why unsafe code exists, its invariants, maintenance, and exposure to
untrusted inputs.

## Bad

```text
# Dependency updates ship without an advisory, license, or source review.
```

## Good

### CI Baseline

```yaml
# Run after installing the tools in the pinned CI image.
- run: cargo audit
- run: cargo deny check bans licenses sources
- run: cargo geiger --all-features
```

Keep any `cargo deny` exceptions in version control with a reason and expiry;
silently suppressing an advisory turns a review decision into invisible risk.
Pin all three tool versions in CI and choose feature combinations that represent
what you ship; `--all-features` can be misleading for mutually exclusive
features.

Organizations that review third-party source can use
[`cargo-vet`](https://mozilla.github.io/cargo-vet/) to record audits, trusted
publisher criteria, and imported audits in version control. It complements the
checks above: audit records do not scan for RustSec advisories, enforce license
policy, or prove that every runtime configuration is safe.

## See Also

- [unsafe-miri-ci](./unsafe-miri-ci.md) - check unsafe-code behavior
- [proj-workspace-deps](./proj-workspace-deps.md) - centralize dependency versions
- [perf-ahash](./perf-ahash.md) - choose hashers with an appropriate threat model

## Source

Distilled from [Hardening Rust Code For Production](https://corrode.dev/blog/hardening-rust/)
and [Pitfalls of Safe Rust](https://corrode.dev/blog/pitfalls-of-safe-rust/).

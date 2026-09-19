# opt-lto-release

> Measure ThinLTO or fat LTO for performance-sensitive final binaries

## Why It Matters

Link-Time Optimization (LTO) can expose cross-crate inlining, dead-code
elimination, and devirtualization opportunities. Its effect is workload- and
toolchain-dependent: it can improve speed or size, do nothing material, or make
builds much slower. Benchmark representative final binaries before selecting a
setting. Libraries should generally leave final-link profile choices to their
consumers.

## Bad

```toml
# Cargo.toml - default release profile
[profile.release]
opt-level = 3
# Cargo's default still performs local thin LTO in some profile configurations.
```

## Good

```toml
# Cargo.toml - a profile to evaluate for a final binary
[profile.release]
opt-level = 3
lto = "thin"         # Try "thin" first; measure against false and "fat"
```

## LTO Options Explained

```toml
# Default profile behavior; may perform thin-local LTO between a crate's CGUs
lto = false

# Disable all LTO, including thin-local LTO
lto = "off"

# Thin LTO - fast compilation, most benefits
lto = "thin"

# Fat LTO - broader and usually slower; not guaranteed to be faster at runtime
lto = "fat"
# Equivalent to:
lto = true

```

Exact build-time, size, and runtime effects depend on the program. ThinLTO is
often the practical first experiment; fat LTO considers more code together but
is not universally faster or smaller.

## Evidence from Production

Many production crates enable fat LTO and `codegen-units = 1` in their release
profiles for maximum performance. For example, ripgrep ships a `release-lto`
profile (see the Cargo Book for profile documentation:
<https://doc.rust-lang.org/cargo/reference/profiles.html>):

```toml
# A common pattern in performance-critical crates
[profile.release]
overflow-checks = true
lto = "fat"
codegen-units = 1

# Named profile for explicit LTO builds (e.g. ripgrep's release-lto)
[profile.release-lto]
inherits = "release"
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"
strip = "symbols"
```

## Complete Optimized Profile

```toml
[profile.release]
opt-level = 3        # Aggressive speed optimization
lto = "fat"          # Link-time optimization
codegen-units = 1    # Single codegen unit for better optimization
panic = "abort"      # Remove panic unwinding code
strip = true         # Strip symbols
debug = false        # No debug info

# For benchmarking (need some debug info for profiling)
[profile.bench]
inherits = "release"
debug = true
strip = false

# Fast dev builds with optimized dependencies
[profile.dev]
opt-level = 0
debug = true

[profile.dev.package."*"]
opt-level = 3        # Optimize dependencies even in dev
```

## When to Use Each

| Situation             | LTO Setting                                                 |
| --------------------- | ----------------------------------------------------------- |
| Development           | `false` (fast compiles)                                     |
| CI builds             | Match the artifact being validated, or prefer faster builds |
| Release binaries      | Benchmark `false`, `"thin"`, and `"fat"`                    |
| Libraries (crates.io) | `false` (users choose)                                      |

## Measuring Impact

```bash
# Build without LTO
cargo build --release
hyperfine ./target/release/myapp

# Build with LTO
# (after adding lto = "fat" to Cargo.toml)
cargo build --release
hyperfine ./target/release/myapp

# Compare binary sizes
ls -la target/release/myapp
```

## See Also

- [opt-codegen-units](opt-codegen-units.md) - Trade compile parallelism for optimization scope
- [opt-pgo-profile](opt-pgo-profile.md) - Profile-guided optimization
- [perf-release-profile](perf-release-profile.md) - Full release profile settings

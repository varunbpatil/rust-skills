# opt-codegen-units

> Trade release build parallelism for optimization with fewer codegen units

## Why It Matters

Cargo splits a crate into multiple codegen units (CGUs) so LLVM can compile them
in parallel. Fewer CGUs give each LLVM invocation a wider view but reduce build
parallelism. `codegen-units = 1` is a useful configuration to benchmark for a
final performance-sensitive binary, not a universal production default; LTO,
incremental compilation, dependencies, and workload can change the result.

## Bad

```toml
# Cargo.toml - default settings
[profile.release]
# codegen-units defaults to 16
# Fast to compile, but misses optimization opportunities
```

## Good

```toml
# Cargo.toml - a configuration to benchmark
[profile.release]
codegen-units = 1  # Single unit = better optimization
lto = true         # Link-time optimization
opt-level = 3      # Aggressive speed optimization
```

## What codegen-units Affects

| Codegen Units | Typical tradeoff                                                     |
| ------------- | -------------------------------------------------------------------- |
| More          | More LLVM parallelism; less optimization visibility per unit         |
| Fewer         | Less parallelism; more visibility per unit                           |
| 1             | Widest within-crate view, but not guaranteed best end-to-end results |

## How It Works

```rust
// With codegen-units = 16:
// - Crate split into 16 independent compilation units
// - Compiled in parallel
// - Limited visibility between units for optimization

// With codegen-units = 1:
// - Entire crate in single unit
// - LLVM sees all code at once
// - Can inline across module boundaries
// - May enable better dead-code elimination and constant propagation
```

## Full Release Profile

```toml
[profile.release]
# Maximum runtime performance
opt-level = 3
lto = "fat"
codegen-units = 1
panic = "abort"      # Smaller binary, slight perf gain
strip = true         # Smaller binary

[profile.release-with-debug]
# Performance with debugging ability
inherits = "release"
debug = true         # Keep debug symbols
strip = false

[profile.bench]
# For benchmarking
inherits = "release"
```

## Build Time Trade-offs

```bash
# Default release build (fast compile)
cargo build --release

# Optimized release build (slow compile, fast runtime)
# With codegen-units = 1, lto = "fat"
cargo build --release
# Compare wall-clock build time, artifact size, and representative benchmarks.
```

## Per-Profile Configuration

```toml
# Fast debug builds
[profile.dev]
codegen-units = 256  # Maximum parallelism

# Fast CI builds
[profile.ci]
inherits = "release"
codegen-units = 16   # Balance compile time vs runtime
lto = "thin"         # Faster than "fat"

# Production release
[profile.production]
inherits = "release"
codegen-units = 1
lto = "fat"
```

## When to Use What

```rust
// codegen-units = 16 (default)
// - Development builds
// - CI where compile time matters
// - When runtime performance isn't critical

// codegen-units = 1
// - A candidate for performance-critical final artifacts
// - One configuration to include in benchmarking
```

## Measuring Impact

```bash
# Build with different settings
cargo build --release

# Benchmark
cargo bench

# Compare binary sizes
ls -lh target/release/my_binary

# Profile runtime
perf stat ./target/release/my_binary
```

## See Also

- [opt-lto-release](./opt-lto-release.md) - Link-time optimization
- [opt-pgo-profile](./opt-pgo-profile.md) - Profile-guided optimization
- [opt-target-cpu](./opt-target-cpu.md) - CPU-specific optimization

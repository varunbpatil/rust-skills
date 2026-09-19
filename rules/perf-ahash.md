# perf-ahash

> Use a faster hasher (`ahash` / `FxHashMap`) when DoS resistance is not needed

## Why It Matters

Rust's default `HashMap` uses a randomly keyed hasher selected to resist
algorithmic-complexity attacks. Other hashers can improve throughput for some
key distributions, especially internal integer IDs, but the result is workload-
and version-dependent. Random seeding alone does not make a non-cryptographic
hasher suitable for adversarial keys. Switch only after profiling, and keep the
standard hasher (or perform a dedicated threat analysis) at untrusted-input
boundaries.

## Bad

```rust
use std::collections::HashMap;

// Using the default SipHash hasher for compiler-internal integer keys —
// DoS resistance is wasted cost here.
fn build_id_map(ids: &[(u32, String)]) -> HashMap<u32, String> {
    ids.iter().cloned().collect()
}
```

## Good

```rust
// aHash is randomized and often fast, but does not claim cryptographic
// HashDoS resistance. Use it for trusted inputs after measurement.
use ahash::AHashMap;

fn build_id_map_ahash(ids: &[(u32, String)]) -> AHashMap<u32, String> {
    ids.iter().cloned().collect()
}

// FxHashMap (rustc-hash): fastest option, but uses a predictable hash function.
// Only for trusted integer or pointer keys where hash flooding is not a concern
// (e.g., compiler internals, in-process caches keyed by integer IDs).
use rustc_hash::FxHashMap;

type NodeMap<V> = FxHashMap<u32, V>;

fn build_node_map(nodes: &[(u32, String)]) -> NodeMap<String> {
    let mut map = NodeMap::with_capacity_and_hasher(
        nodes.len(),
        Default::default(),
    );
    map.extend(nodes.iter().cloned());
    map
}

// Convenient type aliases to avoid repeating the hasher parameter
use std::collections::HashMap;
use rustc_hash::FxBuildHasher;

type FastMap<K, V> = HashMap<K, V, FxBuildHasher>;

fn fast_map_example() -> FastMap<u32, u64> {
    FastMap::with_capacity_and_hasher(64, FxBuildHasher)
}
```

## Hasher Selection Guide

| Hasher        | Crate         | DoS-resistant                 | Speed              | Use when                                         |
| ------------- | ------------- | ----------------------------- | ------------------ | ------------------------------------------------ |
| `SipHash-1-3` | std (default) | Yes                           | Baseline           | Keys from untrusted external input               |
| `ahash`       | `ahash`       | Not a cryptographic guarantee | Workload-dependent | Trusted keys after profiling                     |
| `FxHash`      | `rustc-hash`  | No                            | Fastest            | Trusted integer/pointer keys, compiler internals |
| `gxhash`      | `gxhash`      | Consult crate threat model    | Workload-dependent | Specialized measured workloads                   |

## Key Points

- **Profile first**: switch hashers only after confirming map operations appear in profiler output.
- `ahash::AHashMap` is API-compatible for many uses, but random per-process keys
  are not a substitute for a documented adversarial-input guarantee.
- `FxHashMap` is what rustc uses internally; it is predictable, so never expose it to externally-supplied keys.
- Pass `with_capacity` when the final size is known — it applies regardless of hasher choice.

## See Also

- [perf-entry-api](perf-entry-api.md) - avoid redundant lookups with the entry API
- [perf-profile-first](perf-profile-first.md) - profile before optimizing
- [mem-with-capacity](mem-with-capacity.md) - pre-allocate collections when size is known

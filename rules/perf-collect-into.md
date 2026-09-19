# perf-collect-into

> Use `Extend::extend` to collect into reusable containers on stable Rust

## Why It Matters

`Extend::extend` inserts iterator results into an existing collection and can
reuse retained capacity. The similarly named `Iterator::collect_into` remains
unstable on Rust 1.98, so stable APIs and examples should use `extend`.

> **Note:** `collect_into` is currently **nightly-only** (requires `#![feature(iter_collect_into)]`, tracking issue [#94780](https://github.com/rust-lang/rust/issues/94780)). On stable Rust, use `extend()` instead — see the Stable Alternative section below.

## Bad

```rust
// Allocates new Vec each time
fn process_batches(batches: Vec<Vec<i32>>) -> Vec<Vec<i32>> {
    batches.into_iter()
        .map(|batch| {
            batch.into_iter()
                .filter(|x| *x > 0)
                .collect::<Vec<_>>()  // New allocation per batch
        })
        .collect()
}

// Can't reuse cleared buffer
fn filter_loop(data: &[Vec<i32>]) {
    for batch in data {
        let filtered: Vec<_> = batch.iter()
            .filter(|&&x| x > 0)
            .copied()
            .collect();  // New allocation each iteration
        process(&filtered);
    }
}
```

## Good

### Stable: `extend`

```rust
// Stable approach: reuse buffer with extend
fn filter_loop(data: &[Vec<i32>]) {
    let mut buffer = Vec::new();

    for batch in data {
        buffer.clear();  // Keep allocation
        buffer.extend(
            batch.iter()
                .filter(|&&x| x > 0)
                .copied()
        );
        process(&buffer);
    }
}
```

## Nightly: collect_into

```rust
#![feature(iter_collect_into)]

// Reuse buffer with collect_into (nightly only)
fn filter_loop_nightly(data: &[Vec<i32>]) {
    let mut buffer = Vec::new();

    for batch in data {
        buffer.clear();  // Keep allocation
        batch.iter()
            .filter(|&&x| x > 0)
            .copied()
            .collect_into(&mut buffer);
        process(&buffer);
    }
}

```

## Stable Alternative: extend

On stable Rust, `extend()` is equivalent and idiomatic:

```rust
fn reuse_buffer(data: &[Vec<i32>]) {
    let mut buffer = Vec::new();

    for batch in data {
        buffer.clear();
        buffer.extend(batch.iter().filter(|&&x| x > 0).copied());
        process(&buffer);
    }
}
```

## Pattern: Transform and Reuse

```rust
fn transform_batches(batches: &[Vec<RawData>]) -> Vec<ProcessedData> {
    let mut temp = Vec::new();
    let mut all_results = Vec::new();

    for batch in batches {
        temp.clear();
        temp.extend(batch.iter().map(ProcessedData::from));

        // Process temp, append to results
        all_results.extend(temp.drain(..).filter(|p| p.is_valid()));
    }

    all_results
}
```

## Supported Collections

`extend()` works with types implementing `Extend`:

```rust
use std::collections::{HashSet, VecDeque};

let mut vec = Vec::new();
let mut set = HashSet::new();
let mut deque = VecDeque::new();

vec.extend(0..10);
set.extend(0..10);
deque.extend(0..10);
```

## Comparison

| Method                              | Allocation    | Buffer Reuse |
| ----------------------------------- | ------------- | ------------ |
| `.collect()`                        | New each time | No           |
| `.collect_into(&mut buf)` (nightly) | Reuses buffer | Yes          |
| `buf.extend(iter)`                  | Reuses buffer | Yes          |

## See Also

- [perf-drain-reuse](./perf-drain-reuse.md) - Drain for reuse
- [mem-reuse-collections](./mem-reuse-collections.md) - Collection reuse
- [perf-extend-batch](./perf-extend-batch.md) - Batch extensions

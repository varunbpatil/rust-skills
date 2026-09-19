# perf-iter-over-index

> Prefer iterators when they express traversal more clearly; use indices when the index is part of the problem

## Why It Matters

Manual indexing makes off-by-one and mismatched-length bugs easy to write.
Iterator adapters express traversal and relationships directly. They can also
make bounds-check elimination and vectorization easier for LLVM, but Rust does
not guarantee either optimization: well-structured indexed loops can compile
just as efficiently. Preserve semantics first, then inspect generated code or
benchmark when the loop is actually hot.

## Bad

```rust
fn dot_product(a: &[f64], b: &[f64]) -> f64 {
    // Silently truncates to the shorter input and couples traversal to an index.
    let mut sum = 0.0;
    for i in 0..a.len().min(b.len()) {
        sum += a[i] * b[i];
    }
    sum
}

fn double_values(data: &mut [i32]) {
    for i in 0..data.len() {
        data[i] *= 2;
    }
}
```

## Good

```rust
fn dot_product(a: &[f64], b: &[f64]) -> f64 {
    assert_eq!(a.len(), b.len(), "vectors must have equal dimensions");
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

fn double_values(data: &mut [i32]) {
    for value in data {
        *value *= 2;
    }
}
```

The assertion preserves an equal-dimension contract; using `zip` alone would
silently change behavior by truncating unequal inputs.

## When Indices Are Appropriate

Use indices when they carry meaning, when traversal is deliberately
non-sequential, or when an algorithm relates several positions:

```rust
fn adjacent_differences(values: &[i64]) -> Vec<i64> {
    values.windows(2).map(|pair| pair[1] - pair[0]).collect()
}

fn report_positions(values: &[i64]) {
    for (index, value) in values.iter().enumerate() {
        println!("{index}: {value}");
    }
}
```

For a genuinely index-driven algorithm, safe indexing is the default. Do not
introduce `get_unchecked` without profiling evidence and a documented proof of
the bounds invariant.

## Optimization Notes

- LLVM may eliminate bounds checks and vectorize either indexed or iterator
  forms.
- Iterator syntax is not a performance guarantee, and indexing is not proof of
  a bounds check in the final machine code.
- Prefer the version that states the algorithm's invariants most clearly.
- Use benchmarks or assembly inspection for performance-sensitive code.

## See Also

- [perf-iter-lazy](./perf-iter-lazy.md) - keep iterator pipelines lazy
- [opt-bounds-check](./opt-bounds-check.md) - structure hot loops for optimization
- [conc-rayon-par-iter](./conc-rayon-par-iter.md) - parallelize suitable CPU work

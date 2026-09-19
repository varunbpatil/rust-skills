# num-float-compare

> Choose exact, approximate, or total-order float comparison to match the domain

## Why It Matters

Floating-point arithmetic is not exact: `0.1 + 0.2 == 0.3` evaluates to
`false` because these values are not all represented exactly in binary.
Approximate physical or computed quantities usually need a domain-chosen
absolute/relative tolerance. Exact equality remains appropriate for values that
were copied, for zero and sentinel checks whose IEEE semantics are intended, or
when the domain specifies exact representation. For sorting, `partial_cmp`
returns `None` on NaN; use `total_cmp` when the IEEE total order is appropriate.

## Bad

```rust
fn is_unit_length(x: f64, y: f64) -> bool {
    (x * x + y * y).sqrt() == 1.0  // almost always false due to rounding
}

fn sort_scores(scores: &mut Vec<f64>) {
    scores.sort_by(|a, b| a.partial_cmp(b).unwrap());
    // panics (unwrap on None) if any score is NaN
}
```

## Good

```rust
// approximate equality with an absolute epsilon
fn approx_eq(a: f64, b: f64, epsilon: f64) -> bool {
    (a - b).abs() < epsilon
}

fn is_unit_length(x: f64, y: f64) -> bool {
    approx_eq((x * x + y * y).sqrt(), 1.0, 1e-9)
}

// IEEE total ordering: positive NaNs sort after positive infinity; negative
// NaNs sort before negative infinity (consistent and non-panicking).
fn sort_scores(scores: &mut Vec<f64>) {
    scores.sort_by(|a, b| a.total_cmp(b));
}

// direct NaN check when needed
fn safe_reciprocal(x: f64) -> Option<f64> {
    if x == 0.0 || x.is_nan() {
        None
    } else {
        Some(1.0 / x)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn float_addition_is_not_exact() {
        assert_ne!(0.1_f64 + 0.2, 0.3);  // IEEE 754 rounding
        assert!(approx_eq(0.1 + 0.2, 0.3, 1e-10));
    }

    #[test]
    fn nan_is_not_equal_to_itself() {
        let nan = f64::NAN;
        assert_ne!(nan, nan);  // NaN != NaN by IEEE 754
    }

    #[test]
    fn total_cmp_handles_nan() {
        let mut v = vec![3.0_f64, f64::NAN, 1.0, f64::NAN, 2.0];
        sort_scores(&mut v);
        // NaN values sort to the end; finite values are in order
        assert_eq!(&v[..3], &[1.0, 2.0, 3.0]);
        assert!(v[3].is_nan());
        assert!(v[4].is_nan());
    }

    #[test]
    fn unit_length_uses_tolerance() {
        assert!(is_unit_length(1.0, 0.0));
        assert!(is_unit_length(0.6, 0.8));  // 3-4-5 right triangle scaled
    }
}
```

## Key Points

- **Epsilon choice**: an absolute epsilon (`1e-9`) is simple but wrong for very large or very small values. For general-purpose code, a relative epsilon `(a - b).abs() / a.abs().max(b.abs()) < epsilon` is more robust — but requires handling the zero case.
- **`f64::total_cmp`** defines a strict total order: `-NaN < -∞ < … < -0.0 < +0.0 < … < +∞ < NaN`. It never panics and is available on `f32` and `f64`.
- **`is_nan` / `is_infinite` / `is_finite`**: use these predicates before arithmetic on untrusted floats.
- **Equality on `f32`/`f64` with `==`** follows IEEE numeric equality; it is not
  bit equality (`-0.0 == 0.0`, and NaN is unequal to itself). Use `to_bits()`
  when the bit pattern is what matters.

## Ecosystem Types

Use [`ordered-float`](https://crates.io/crates/ordered-float) when floats must be
keys in a `HashMap`/`BTreeMap` or members of a set. Choose `OrderedFloat` only
after accepting its defined equality and ordering semantics for NaN and signed
zero; use `NotNan` when NaN must be rejected at construction. For repeated
approximate assertions or comparisons, a dedicated crate such as
[`float-cmp`](https://crates.io/crates/float-cmp) avoids duplicating incomplete
absolute/relative/ULP comparison logic. The tolerance still belongs to the
domain rather than the crate.

When the domain requires exact base-10 arithmetic, such as fixed-scale money,
use a decimal type instead of choosing an epsilon for binary floats.
[`rust_decimal`](https://crates.io/crates/rust_decimal) provides bounded
fixed-precision decimal arithmetic; [`bigdecimal`](https://crates.io/crates/bigdecimal)
provides arbitrary-precision decimals at a higher storage and computation cost.
Define rounding and scale policy explicitly whichever representation you use.

## See Also

- [num-overflow-explicit](num-overflow-explicit.md) - handle integer overflow explicitly
- [type-newtype-validated](type-newtype-validated.md) - enforce domain-specific numeric invariants at construction

## References

- [`f64::total_cmp`](https://doc.rust-lang.org/std/primitive.f64.html#method.total_cmp)
- [The Rust Reference: floating-point types](https://doc.rust-lang.org/reference/types/numeric.html#floating-point-types)

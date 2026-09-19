# num-cast-try-from

> Avoid `as` for narrowing casts; use `From` for widening and `TryFrom` for narrowing

## Why It Matters

The `as` cast silently truncates or wraps on narrowing (`300u32 as u8 == 44`) and produces surprising results on float-to-integer conversion (values outside range saturate to the type's min/max since Rust 1.45, but `NaN` becomes `0`). These behaviors are easy to miss during code review. Standard-library `From`/`Into` implementations are infallible and lossless in the relevant sense; `TryFrom`/`TryInto` return `Result` and make fallibility explicit. Custom trait implementations must uphold those conventions themselves.

## Bad

```rust
fn narrow(x: u32) -> u8 {
    x as u8  // silently truncates: 300 becomes 44
}

fn to_index(f: f64) -> usize {
    f as usize  // NaN becomes 0, negatives become 0, may truncate
}

fn widen(x: u8) -> u32 {
    x as u32  // works, but hides that this is always safe
}
```

## Good

```rust
use std::convert::TryFrom;

// widening: the standard library provides this lossless conversion
fn widen(x: u8) -> u32 {
    u32::from(x)
    // or: x.into()
}

// narrowing: TryFrom makes the failure case explicit
fn narrow(x: u32) -> Result<u8, <u8 as TryFrom<u32>>::Error> {
    u8::try_from(x)
    // or: x.try_into()
}

// float → integer: validate the range manually before casting
fn float_to_index(f: f64, len: usize) -> Option<usize> {
    // On 64-bit targets usize::MAX rounds upward when converted to f64, so use
    // a strict bound before casting and check the resulting index separately.
    if !f.is_finite() || f < 0.0 || f >= usize::MAX as f64 {
        return None;
    }
    let index = f as usize; // fractional values deliberately truncate
    (index < len).then_some(index)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::convert::TryFrom;

    #[test]
    fn widen_is_lossless() {
        assert_eq!(widen(255), 255u32);
    }

    #[test]
    fn narrow_errors_on_overflow() {
        assert!(narrow(300).is_err());
        assert_eq!(narrow(200), Ok(200u8));
    }

    #[test]
    fn float_to_index_rejects_nan_and_negative() {
        assert_eq!(float_to_index(f64::NAN, 10), None);
        assert_eq!(float_to_index(-1.0, 10), None);
        assert_eq!(float_to_index(3.9, 10), Some(3));
    }

    #[test]
    fn as_cast_truncation_footgun() {
        // demonstrating why `as` is dangerous for narrowing:
        let x: u32 = 300;
        assert_eq!(x as u8, 44);  // 300 % 256 == 44 — silently wrong
    }
}
```

## Key Points

- Standard-library `From` implementations follow the convention that the
  conversion is infallible and lossless in the relevant sense. The trait system
  cannot enforce that convention for custom implementations. `u8::from(u32)`
  is therefore not implemented; use `u8::try_from(value)` for narrowing.
- `TryFrom` returns `Result<T, TryFromIntError>` from the standard library — no external crates needed.
- Reserve `as` for:
  - Pointer casts (e.g., `*const u8 as *mut u8`) that are intentional.
  - Float-to-integer when you have verified the range and documented the intent.
  - `usize` ↔ pointer-sized integer when exact semantics are required.
- When using `.try_into()`, the turbofish or type annotation is often needed to help inference: `let n: u8 = x.try_into()?;`

## See Also

- [conv-tryfrom-fallible](conv-tryfrom-fallible.md) - implement `TryFrom` for your own fallible conversions
- [num-overflow-explicit](num-overflow-explicit.md) - handle integer overflow explicitly with `checked_`/`saturating_`/`wrapping_`

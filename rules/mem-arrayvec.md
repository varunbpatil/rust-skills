# mem-arrayvec

> Use `ArrayVec<T, N>` for fixed-capacity collections that never heap-allocate

## Why It Matters

`ArrayVec` from the `arrayvec` crate provides a Vec-like API with a compile-time
maximum capacity and stores elements inline wherever the `ArrayVec` value lives
(which is not necessarily the stack). Unlike `SmallVec`, the collection itself
does not spill to a separate heap allocation; exceeding capacity returns an
error through fallible methods or panics through infallible ones. Element types
may of course allocate internally.

## Bad

```rust
// A non-empty Vec stores elements in a separate heap allocation.
fn parse_options(input: &str) -> Vec<Option> {
    let mut options = Vec::new();  // Heap allocation
    for part in input.split(',').take(8) {  // Know we never exceed 8
        options.push(parse_option(part));
    }
    options
}

// Or SmallVec when you truly can't exceed capacity
use smallvec::SmallVec;
fn get_flags() -> SmallVec<[Flag; 4]> {
    // SmallVec CAN heap-allocate if pushed beyond 4
    // That might be unexpected in no-alloc contexts
}
```

## Good

```rust
use arrayvec::ArrayVec;

// The collection's element storage is inline; element values may allocate.
fn parse_options(input: &str) -> ArrayVec<Option<u32>, 8> {
    let mut options = ArrayVec::new();
    for part in input.split(',') {
        if options.try_push(parse_option(part)).is_err() {
            break;  // Capacity reached, stop
        }
    }
    options
}

// For embedded/no_std contexts
fn collect_readings() -> ArrayVec<SensorReading, 16> {
    let mut readings = ArrayVec::new();
    for sensor in SENSORS.iter() {
        readings.push(sensor.read());  // Panics if > 16
    }
    readings
}
```

## ArrayVec vs SmallVec vs Vec

| Type               | Element storage  | Separate allocation                 | Use When                              |
| ------------------ | ---------------- | ----------------------------------- | ------------------------------------- |
| `Vec<T>`           | Out of line      | When non-zero capacity is allocated | Unknown size, may grow                |
| `SmallVec<[T; N]>` | Inline through N | After spilling beyond N             | Usually small, occasionally large     |
| `ArrayVec<T, N>`   | Inline           | Not for the collection's storage    | Hard limit, no allocation for storage |

## API Patterns

```rust
use arrayvec::ArrayVec;

let mut arr: ArrayVec<i32, 4> = ArrayVec::new();

// Push with potential panic (like Vec)
arr.push(1);
arr.push(2);

// Safe push - returns Err if full
match arr.try_push(3) {
    Ok(()) => println!("Added"),
    Err(err) => println!("Full, couldn't add {}", err.element()),
}

// Check capacity
assert!(arr.len() < arr.capacity());

// Remaining capacity
let remaining = arr.remaining_capacity();

// Is it full?
if arr.is_full() {
    arr.pop();
}

// From iterator with limit
let arr: ArrayVec<_, 10> = (0..100)
    .filter(|x| x % 2 == 0)
    .take(10)  // Important: don't exceed capacity
    .collect();
```

## ArrayString for Stack Strings

```rust
use arrayvec::ArrayString;
use std::fmt::Write; // brings the write! target trait into scope

// Stack-allocated string with max capacity
let mut s: ArrayString<64> = ArrayString::new();
s.push_str("Hello, ");
s.push_str("world!");

// No heap allocation for small strings
fn format_code(code: u32) -> ArrayString<16> {
    let mut s = ArrayString::new();
    write!(&mut s, "CODE-{:04}", code).unwrap();
    s
}
```

## When NOT to Use ArrayVec

```rust,ignore
// ❌ When size varies widely
fn parse_json_array(json: &str) -> ArrayVec<Value, ???> {
    // What capacity? JSON arrays can be any size
}

// ❌ When capacity is very large
let big: ArrayVec<u8, 1_000_000> = ArrayVec::new();  // 1MB on stack = bad

// ✅ Use SmallVec or Vec instead for these cases
```

## Cargo.toml

```toml
[dependencies]
arrayvec = "0.7"
```

## See Also

- [mem-smallvec](./mem-smallvec.md) - When heap fallback is acceptable
- [mem-with-capacity](./mem-with-capacity.md) - Pre-allocating Vec capacity
- [own-move-large](./own-move-large.md) - Large stack types considerations

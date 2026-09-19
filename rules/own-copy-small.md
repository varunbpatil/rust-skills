# own-copy-small

> Implement `Copy` for small value types with implicit-copy semantics

## Why It Matters

Types that implement `Copy` are implicitly duplicated on assignment instead of
moved. This is ergonomic for plain values such as coordinates and numeric IDs,
where an implicit duplicate is unsurprising. Size matters, but there is no
universal byte cutoff: semantics, copy frequency, public-API compatibility, and
measured cost matter too. Do not add `Copy` to resource handles or types whose
duplication should remain visible even when all fields technically permit it.

## Bad

```rust
// Small type without Copy - requires explicit clone
#[derive(Clone, Debug)]
struct Point {
    x: f64,
    y: f64,
}

fn distance(p1: Point, p2: Point) -> f64 {
    ((p2.x - p1.x).powi(2) + (p2.y - p1.y).powi(2)).sqrt()
}

let origin = Point { x: 0.0, y: 0.0 };
let target = Point { x: 3.0, y: 4.0 };

let d1 = distance(origin.clone(), target.clone()); // Tedious
let d2 = distance(origin.clone(), target.clone()); // Every use needs clone
// origin and target still usable but verbose
```

## Good

```rust
// Small type with Copy - implicit duplication
#[derive(Clone, Copy, Debug)]
struct Point {
    x: f64,
    y: f64,
}

fn distance(p1: Point, p2: Point) -> f64 {
    ((p2.x - p1.x).powi(2) + (p2.y - p1.y).powi(2)).sqrt()
}

let origin = Point { x: 0.0, y: 0.0 };
let target = Point { x: 3.0, y: 4.0 };

let d1 = distance(origin, target); // Implicitly copied
let d2 = distance(origin, target); // Still works!
// origin and target remain valid
```

## Copy Requirements

A type can implement `Copy` only if:

1. All fields implement `Copy`
2. No custom `Drop` implementation
3. No heap-allocated data (`String`, `Vec`, `Box`, etc.)

```rust
// ✅ Can be Copy
#[derive(Clone, Copy)]
struct Color {
    r: u8,
    g: u8,
    b: u8,
    a: u8,
}

// ❌ Cannot be Copy - contains String
#[derive(Clone)]
struct Person {
    name: String,  // String is not Copy
    age: u32,
}

// ❌ Cannot be Copy - has Drop
struct FileHandle {
    fd: i32,
}
impl Drop for FileHandle {
    fn drop(&mut self) { /* close file */ }
}
```

## Decision Guidelines

| Property                                            | Guidance                                                      |
| --------------------------------------------------- | ------------------------------------------------------------- |
| Plain, small value with cheap implicit duplication  | Usually implement `Copy`                                      |
| Resource identity or duplication should be explicit | Keep only `Clone`, or neither                                 |
| Large value copied in a hot path                    | Prefer borrowing and measure                                  |
| Public type likely to gain non-`Copy` fields        | Consider leaving `Copy` off; removing it later breaks callers |

```rust
use std::mem::size_of;

#[derive(Clone, Copy)]
struct SmallId(u64); // 8 bytes ✅

#[derive(Clone, Copy)]
struct Rect { x: f32, y: f32, w: f32, h: f32 } // 16 bytes ✅

#[derive(Clone)] // Keep an expensive duplication explicit
struct Transform {
    matrix: [[f64; 3]; 3],
}
```

## Common Copy Types

Standard library types that are `Copy`:

- All primitives: `i32`, `f64`, `bool`, `char`, etc.
- Shared references: `&T` (note: `&mut T` is NOT `Copy` — copying a mutable reference would alias it, so it is reborrowed instead)
- Raw pointers: `*const T`, `*mut T`
- Function pointers: `fn(T) -> U`
- Tuples of `Copy` types: `(i32, f64)`
- Arrays of `Copy` types: `[u8; 32]`
- `Option<T>` where `T: Copy`
- `PhantomData<T>`

## See Also

- [own-clone-explicit](./own-clone-explicit.md) - When Clone without Copy is appropriate
- [type-newtype-ids](./type-newtype-ids.md) - Newtype pattern often uses Copy

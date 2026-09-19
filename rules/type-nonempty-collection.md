# type-nonempty-collection

> Use an established non-empty collection type or a validated domain newtype when emptiness is invalid

## Why It Matters

Repeated `is_empty()` checks spread an invariant across callers. A non-empty
type validates once and makes it impossible for later code to index an empty
collection accidentally.

## Bad

```rust
fn primary_recipient(recipients: &[String]) -> &str {
    recipients
        .first()
        .expect("recipient list was assumed to be non-empty")
}
```

## Good

For a general-purpose, `Vec`-like collection, prefer the maintained
[`vec1`](https://crates.io/crates/vec1) crate over rebuilding its API and trait
implementations:

```toml
[dependencies]
vec1 = "1"
```

```rust
use vec1::{vec1, Vec1};

fn primary_recipient(recipients: &Vec1<String>) -> &str {
    recipients.first()
}

fn configured_recipients() -> Vec1<String> {
    vec1!["alerts@example.com".to_owned()]
}

fn parse_recipients(values: Vec<String>) -> Result<Vec1<String>, vec1::Size0Error> {
    Vec1::try_from_vec(values)
}
```

The `vec1!` macro rejects an empty literal, while `Vec1::try_from_vec` validates
data arriving at runtime. The crate also offers optional `serde`, `no_std`, and
`SmallVec1` support.

The maintained [`nonempty`](https://crates.io/crates/nonempty) crate is another
good choice when its explicit `head` plus `tail` representation and functional
collection operations fit the domain. Use a fixed-size array when the exact
length is known statically.

Define a custom newtype when the domain requires validation or behavior beyond
non-emptiness, or when exposing a third-party collection type would unduly
constrain a public API. Accept external vectors through a fallible conversion
rather than requiring every caller to repeat the check:

```rust
struct NonEmpty<T> { first: T, rest: Vec<T> }

impl<T> TryFrom<Vec<T>> for NonEmpty<T> {
    type Error = &'static str;

    fn try_from(values: Vec<T>) -> Result<Self, Self::Error> {
        let mut values = values.into_iter();
        let Some(first) = values.next() else {
            return Err("collection must not be empty");
        };
        Ok(Self { first, rest: values.collect() })
    }
}
```

Use a plain `Vec<T>` when emptiness is meaningful rather than invalid.

## See Also

- [type-newtype-validated](./type-newtype-validated.md) - validate at construction
- [api-parse-dont-validate](./api-parse-dont-validate.md) - parse into validated types
- [perf-iter-over-index](./perf-iter-over-index.md) - avoid fragile manual indexing

## Source

Distilled from [Compile-Time Invariants in Rust](https://corrode.dev/blog/compile-time-invariants/).
The article recommends `vec1` for production use and also identifies
`nonempty` as a production-ready implementation.

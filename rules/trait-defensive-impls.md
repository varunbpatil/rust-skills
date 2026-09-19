# trait-defensive-impls

> Destructure evolving structs in manual trait implementations so new fields require a decision

## Why It Matters

A hand-written `PartialEq`, `Hash`, or `Debug` implementation can silently
become wrong when a field is added. Destructuring makes the compiler require an
explicit decision for every new field. Prefer deriving when derive has the
required semantics. When equality and hashing are both implemented, preserve
the contract that equal values always hash equally; make a single deliberate
field-selection decision for the related implementations.

## Bad

```rust
struct Account { id: u64, name: String, updated_at: u64 }

impl PartialEq for Account {
    fn eq(&self, other: &Self) -> bool {
        // Adding a semantic field to `Account` does not force this impl to be reviewed.
        self.id == other.id && self.name == other.name
    }
}
```

## Good

```rust
struct Account { id: u64, name: String, updated_at: u64 }

impl PartialEq for Account {
    fn eq(&self, other: &Self) -> bool {
        let Self { id, name, updated_at: _ } = self;
        let Self { id: other_id, name: other_name, updated_at: _ } = other;
        id == other_id && name == other_name
    }
}
```

## See Also

- [api-common-traits](./api-common-traits.md) - implement standard traits deliberately
- [pat-exhaustive-enum](./pat-exhaustive-enum.md) - preserve compiler-enforced coverage
- [type-display-vs-debug](./type-display-vs-debug.md) - choose diagnostic formatting correctly

## Source

Distilled from [Patterns for Defensive Programming in Rust](https://corrode.dev/blog/defensive-programming/).

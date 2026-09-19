# own-temporary-mutability

> Confine mutation to the smallest scope, then bind the completed value immutably

## Why It Matters

Values are easier to reason about once construction is complete. Keeping `mut`
alive permits accidental later changes and obscures the setup phase.

## Bad

```rust
fn sorted_names(mut names: Vec<String>) -> Vec<String> {
    names.sort();
    // `names` remains mutable throughout unrelated work below.
    record_count(names.len());
    names
}

fn record_count(_: usize) {}
```

## Good

```rust
fn sorted_names(names: Vec<String>) -> Vec<String> {
    let names = {
        let mut names = names;
        names.sort();
        names
    };
    names
}
```

This also makes expression-oriented refactors natural: return the final value
from the setup block instead of carrying a mutable accumulator through unrelated
code.

Use ordinary mutation when it clearly represents an ongoing state transition;
do not introduce a scope solely to satisfy this pattern.

## See Also

- [own-borrow-over-clone](./own-borrow-over-clone.md) - borrow rather than clone
- [api-builder-pattern](./api-builder-pattern.md) - stage complex construction
- [anti-over-abstraction](./anti-over-abstraction.md) - keep implementations simple

## Source

Distilled from [Patterns for Defensive Programming in Rust](https://corrode.dev/blog/defensive-programming/).

# api-avoid-bool-params

> Replace behavior-changing boolean parameters with named methods, enums, or option types

## Why It Matters

`send_report(report, true)` hides what `true` means and becomes fragile as
options grow. A named type makes each choice visible and gives future variants
a place to go. This does not apply to boolean predicates such as `is_empty()`.

## Bad

```rust
fn send_report(report: &str, urgent: bool) {}
send_report("daily", true);
```

## Good

```rust
enum Delivery { Normal, Urgent }

fn send_report(report: &str, delivery: Delivery) {
    let _ = (report, delivery);
}

send_report("daily", Delivery::Urgent);
```

## See Also

- [type-enum-states](./type-enum-states.md) - model exclusive states with enums
- [api-builder-pattern](./api-builder-pattern.md) - construct many optional settings clearly
- [type-no-stringly](./type-no-stringly.md) - avoid ambiguous primitive APIs

## Source

Distilled from [Patterns for Defensive Programming in Rust](https://corrode.dev/blog/defensive-programming/).

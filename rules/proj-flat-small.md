# proj-flat-small

> Keep small projects flat

## Why It Matters

Over-organizing small projects adds navigation overhead without benefit. A project with 5-10 files does not need nested directories. Start flat, add structure only when complexity demands it. Flat files can still preserve boundaries: keep business rules out of HTTP/database glue, even when each boundary is only one file.

## Bad

```
src/
├── user/
│   ├── models/
│   │   └── mod.rs       # Only one small type
│   ├── errors/
│   │   └── mod.rs       # Only one error enum
│   ├── ports/
│   │   └── mod.rs       # Only one trait
│   └── adapters/
│       └── mod.rs       # Only one adapter
└── main.rs              # Mostly empty module wiring
```

## Good

```
src/
├── main.rs              # Thin process entry point
├── lib.rs               # Testable application code and startup wiring
├── config.rs
├── user.rs              # Small feature: types, errors, ports, service
├── user_http.rs         # Inbound adapter, if the application has HTTP
└── user_sqlite.rs       # Outbound adapter, if it persists data
```

## When to Add Structure

| File Count                    | Structure                                                         |
| ----------------------------- | ----------------------------------------------------------------- |
| < 10 files                    | Flat in `src/`                                                    |
| 10-20 files                   | Group the growing feature into a directory                        |
| 20+ files or several adapters | Feature folders with models, errors, ports, service, and adapters |

## Progressive Structuring

### Stage 1: Flat

```
src/
├── main.rs
├── lib.rs
├── config.rs
├── user.rs
└── user_sqlite.rs
```

### Stage 2: Logical Groups

```
src/
├── main.rs
├── lib.rs
├── config.rs
├── user.rs
├── order.rs        # Getting bigger
├── order_item.rs   # Still part of the order feature
├── user_sqlite.rs
└── order_sqlite.rs
```

### Stage 3: Feature Folders

```
src/
├── main.rs
├── lib.rs
├── config.rs
├── user.rs
├── order/          # Now complex enough
│   ├── mod.rs
│   ├── models.rs
│   ├── errors.rs
│   ├── ports.rs
│   ├── service.rs
│   └── adapters/
│       ├── mod.rs
│       └── sqlite.rs
└── user_sqlite.rs
```

## Signs You Need More Structure

- Files exceed 300-500 lines
- Related files are hard to identify
- You're adding many feature-prefixed files (`user_models.rs`, `user_service.rs`, `user_sqlite.rs`)
- New team members get lost
- Same concepts repeated in file names

## Signs of Over-Structure

- Folders with 1-2 files
- `mod.rs` files that only re-export
- Deep nesting for simple concepts
- More lines in module declarations than code

## Prototypes

For a throwaway experiment, a single `main.rs`, concrete types, owned data, and
temporary `unwrap()` calls can shorten the feedback loop. Mark those shortcuts
as prototype-only. Before the code handles real input or becomes a maintained
service, apply the normal error, validation, test, and module-boundary rules;
do not let a prototype's conveniences become production contracts.

Type inference, `anyhow`, `dbg!`, `todo!`, concrete types, and a flat module can
all be useful while discovering the problem. Keep the prototype behind a clear
trust boundary: do not use `unwrap`, `todo!`, or deliberately incomplete input
handling on externally reachable paths.

Before promoting a prototype, replace placeholder panics, identify domain
types and validation boundaries, add representative tests, remove diagnostic
output, review dependencies, and split modules only where change pressure makes
the boundary useful. Prototype convenience is a phase, not an architectural
style that production code must preserve.

## Example: CLI Tool

```
src/
├── main.rs         # Argument parsing, entry point
├── lib.rs          # Command execution and formatting
├── commands.rs     # CLI subcommands
├── config.rs       # Configuration loading
└── output.rs       # Formatting, printing
```

Not:

```
src/
├── cli/
│   └── commands/
│       └── mod.rs
├── config/
│   └── mod.rs
└── presentation/
    └── output/
        └── mod.rs
```

## See Also

- [proj-mod-by-feature](./proj-mod-by-feature.md) - Feature organization
- [proj-lib-main-split](./proj-lib-main-split.md) - Lib/main separation
- [proj-mod-rs-dir](./proj-mod-rs-dir.md) - Multi-file modules

## Source

The prototype guidance is distilled from [Prototyping in Rust](https://corrode.dev/blog/prototyping/).

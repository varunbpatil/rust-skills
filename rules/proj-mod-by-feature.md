# proj-mod-by-feature

> Organize evolving applications by business feature, with domain code inside and adapters at the edge

## Why It Matters

Organizing every model, handler, and repository by technical type scatters a
single business change across the codebase. Organizing by feature keeps a
capability discoverable. Within a feature, a clear dependency direction keeps
HTTP frameworks, database clients, queues, and their errors out of business
logic.

Use this structure when a feature has meaningful business rules or
independently changing infrastructure. It is intentionally more detailed than
the flat layout recommended for small tools; do not create empty layers to
imitate an architecture.

Here, _feature_ names a vertical module for one business capability, including
its domain code, application service, ports, and adapters. _Domain_ names the
business concepts and rules inside that module. A feature may align with a DDD
bounded context, but the feature also owns the adapters that connect its domain
to the outside world.

## Bad

```
src/
├── controllers/
│   ├── user_controller.rs
│   ├── order_controller.rs
│   └── product_controller.rs
├── models/
│   ├── user.rs
│   ├── order.rs
│   └── product.rs
├── services/
│   ├── user_service.rs
│   ├── order_service.rs
│   └── product_service.rs
└── repositories/
    ├── user_repository.rs
    ├── order_repository.rs
    └── product_repository.rs
```

## Good

```
src/
├── main.rs               # Process entry point; invokes application startup
├── lib.rs                # Feature declarations and private-adapter assembly
├── user/
│   ├── mod.rs            # Feature module wiring
│   ├── models.rs         # Domain types
│   ├── errors.rs         # Domain, port-contract, and use-case errors
│   ├── ports.rs          # Application-owned contracts
│   ├── service.rs        # Use cases
│   └── adapters/
│       ├── mod.rs
│       ├── http.rs       # Inbound HTTP translation
│       └── sqlite.rs     # Outbound database implementation
├── order/
│   ├── mod.rs
│   ├── models.rs
│   ├── errors.rs
│   ├── ports.rs
│   ├── service.rs
│   └── adapters/
│       ├── mod.rs
│       ├── http.rs
│       └── sqlite.rs
└── config.rs              # Process configuration, not business logic
```

## Dependency Direction

Within a feature, dependencies point inward:

```
inbound adapter   -->  inbound port  <--  service  -->  outbound ports
                                           ^              ^
startup function  -->  concrete service + adapters  <--  outbound adapters
```

- `models.rs`, `errors.rs`, and `ports.rs` contain no framework, ORM, SQL,
  broker, or transport types.
- `ports.rs` defines application-owned contracts, while `service.rs`
  coordinates business rules through those contracts.
- `adapters/` converts between external types and validated domain types.
- `main.rs` loads process configuration and invokes startup. A package with a
  library target commonly performs composition in a public `run` or `start`
  function; a binary-only crate can compose directly in `main.rs`.

A repository is two different things: its outbound-port trait belongs in
`ports.rs`; a SQLite, Postgres, or remote-API implementation belongs under
`adapters/`. Do not place both in a generic `repository.rs` and let the
infrastructure type leak inward. See [proj-ports-adapters](proj-ports-adapters.md)
for the contracts, error flow, and test seams.

## Small Features

For a small feature, keep the same direction without creating directories
merely for symmetry:

```
src/
├── main.rs               # Process entry point
├── lib.rs
├── user.rs               # Models, errors, ports, and a small service
├── user_http.rs          # Inbound adapter, if needed
└── user_sqlite.rs        # Outbound adapter, if needed
```

Split this into the fuller feature directory when the files become hard to
navigate or the feature gains several adapters. See `proj-flat-small` for a
deliberately simpler application or CLI layout.

## Shared Code

Keep shared code truly cross-cutting:

```
src/
├── config.rs             # Process configuration
├── observability.rs      # Process-wide tracing setup and instrumentation
├── shared/               # Cross-cutting technical code only
│   ├── mod.rs
│   ├── database.rs        # Connection pool/client used by adapters
│   ├── error.rs           # Shared technical or startup errors, not domain errors
│   └── middleware.rs      # App-wide inbound-adapter middleware
├── user/
├── order/
└── lib.rs
```

Do not put feature models, domain errors, ports, services, repositories, or
handlers in `shared/`. A feature adapter may use a shared client or pool, but
it translates vendor and shared technical errors into that feature's own
port-specific errors.

## Nested Features

When a feature grows into a bounded context with distinct sub-capabilities,
retain the same structure at the nested level:

```
src/
└── billing/
    ├── mod.rs
    ├── invoice/
    │   ├── mod.rs
    │   ├── models.rs
    │   ├── errors.rs
    │   ├── ports.rs
    │   ├── service.rs
    │   └── adapters/
    │       ├── mod.rs
    │       └── sqlite.rs
    └── payment/
        ├── mod.rs
        ├── models.rs
        ├── errors.rs
        ├── ports.rs
        ├── service.rs
        └── adapters/
            ├── mod.rs
            └── stripe.rs
```

Keep entities that must change in one atomic business operation together.
Coordinate separate features through the target feature's inbound port or
through events; do not leak a database transaction across feature boundaries.

## Authentication and Authorization

An inbound adapter authenticates transport credentials and converts them into
an application-owned identity or principal. Authorization that expresses a
business rule belongs in the service or domain layer, where non-HTTP callers
cannot bypass it. Framework middleware may reject obviously unauthenticated
requests, but it must not become the only home of domain authorization policy.

## Incremental Adoption

Introduce a port where infrastructure coupling is causing a concrete testing,
replacement, or error-translation problem. Migrate one use case at a time and
keep the application runnable between steps. Avoid rewriting a small CRUD
application into empty layers solely to match the diagram.

## When to Use It

| Situation                                                       | Recommendation                                                |
| --------------------------------------------------------------- | ------------------------------------------------------------- |
| Complex business rules or independently changing infrastructure | Use this feature-and-adapter structure                        |
| Need focused unit tests for error paths                         | Test services against fake port implementations               |
| Small CRUD utility, script, or stable one-off integration       | Prefer the flatter structure until concrete pressure appears  |
| Performance- or memory-critical path                            | Measure conversion and indirection costs before adding layers |

## See Also

- [proj-flat-small](proj-flat-small.md) - keep genuinely small projects flat
- [proj-lib-main-split](proj-lib-main-split.md) - keep binary entry points thin
- [proj-mod-rs-dir](proj-mod-rs-dir.md) - choose a consistent module-file convention
- [proj-ports-adapters](proj-ports-adapters.md) - define inbound and outbound port boundaries
- [proj-feature-boundaries](proj-feature-boundaries.md) - keep feature calls and visibility deliberate
- [api-parse-dont-validate](api-parse-dont-validate.md) - construct valid domain inputs at boundaries
- [anti-over-abstraction](anti-over-abstraction.md) - avoid layers without a concrete need

## Source

The feature-organization guidance is distilled from Angus Morrison's ["Master
hexagonal architecture in Rust"](https://www.howtocodeit.com/guides/master-hexagonal-architecture-in-rust).

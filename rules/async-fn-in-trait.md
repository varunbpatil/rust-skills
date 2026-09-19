# async-fn-in-trait

> Prefer native `async fn` in traits for static dispatch; use an object-safe alternative for `dyn Trait`

## Why It Matters

Since Rust 1.75, you can write `async fn` directly inside trait definitions (AFIT — async functions in traits). This eliminates the `#[async_trait]` proc-macro dependency and removes the hidden `Box<dyn Future>` allocation it inserts on every call. Fewer allocations, no macro expansion overhead, and no extra crate to audit. However, native async fn in traits carries two precise caveats you must understand before migrating.

## Bad

```rust
// requires async_trait crate; boxes every future on the heap
use async_trait::async_trait;

#[derive(Debug)]
enum RepoError {
    Unavailable,
}

#[async_trait]
trait Repo {
    async fn get(&self, id: u64) -> Result<String, RepoError>;
    async fn save(&self, value: String) -> Result<(), RepoError>;
}

struct PgRepo;

#[async_trait]
impl Repo for PgRepo {
    async fn get(&self, id: u64) -> Result<String, RepoError> {
        Ok(format!("row-{id}"))
    }

    async fn save(&self, value: String) -> Result<(), RepoError> {
        let _ = value;
        Ok(())
    }
}
```

## Good

```rust
// native async fn in traits — no macro, no boxing
#[derive(Debug)]
enum RepoError {
    Unavailable,
}

trait Repo {
    async fn get(&self, id: u64) -> Result<String, RepoError>;
    async fn save(&self, value: String) -> Result<(), RepoError>;
}

struct PgRepo;

impl Repo for PgRepo {
    async fn get(&self, id: u64) -> Result<String, RepoError> {
        Ok(format!("row-{id}"))
    }

    async fn save(&self, value: String) -> Result<(), RepoError> {
        let _ = value;
        Ok(())
    }
}
```

## Caveats

**Caveat 1 — not dyn-compatible.** Native async fn in traits is not yet object-safe. You cannot write `Box<dyn Repo>` with the definition above. For dynamic dispatch you have two options:

- Keep `#[async_trait]` (it boxes the future, which makes the trait object-safe).
- Write an object-safe trait whose methods return `Pin<Box<dyn Future<...>>>`.

```rust
#[derive(Debug)]
enum RepoError {
    Unavailable,
}

// trait-variant adds Send bounds; it does not make an async trait dyn-compatible
#[trait_variant::make(RepoSend: Send)]
trait Repo {
    async fn get(&self, id: u64) -> Result<String, RepoError>;
}

// `RepoSend` is the Send-bounded version; neither trait is dyn-compatible.
```

**Caveat 2 — futures are not `Send` by default.** On a multi-threaded Tokio runtime, spawned tasks require `Send` futures. The auto-generated future from a native `async fn` in a trait captures `&self` but does not promise `Send`. If you need `Send`, either:

- Use `#[trait_variant::make(TraitNameSend: Send)]` from the `trait-variant` crate to generate a `Send`-bounded variant.
- Bound the return type explicitly: `fn get(&self, id: u64) -> impl Future<Output = Result<String, RepoError>> + Send`.

```rust
// explicit Send bound on the return future
use std::future::Future;

#[derive(Debug)]
enum RepoError {
    Unavailable,
}

trait Repo {
    fn get(&self, id: u64) -> impl Future<Output = Result<String, RepoError>> + Send;
}
```

If this trait is an application port, make `RepoError` an application-owned, port-specific error. An adapter maps driver failures into it; a service may map it again to a use-case error. See [proj-ports-adapters](proj-ports-adapters.md).

## When to Use Each Approach

| Scenario                                      | Recommended approach                                  |
| --------------------------------------------- | ----------------------------------------------------- |
| Static dispatch only (generics, `impl Trait`) | Native `async fn` in trait                            |
| Need `dyn Trait`                              | `#[async_trait]` or an object-safe boxed-future trait |
| Multi-threaded Tokio, spawned tasks           | `trait-variant` `Send` variant or explicit `+ Send`   |
| Single-threaded runtime / `LocalSet`          | Native `async fn` in trait (no `Send` needed)         |

## See Also

- [anti-type-erasure](anti-type-erasure.md) - prefer `impl Trait` over `Box<dyn Trait>` when possible
- [async-async-fn-bounds](async-async-fn-bounds.md) - use `AsyncFn` bounds for higher-order async functions
- [async-tokio-runtime](async-tokio-runtime.md) - use Tokio for production async runtime
- [proj-ports-adapters](proj-ports-adapters.md) - define ports and error boundaries

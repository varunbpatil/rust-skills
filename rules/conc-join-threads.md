# conc-join-threads

> Keep and join thread handles when completion, failure, or cleanup matters

## Why It Matters

Dropping a `JoinHandle` detaches a thread: its panic can go unnoticed and the
process can exit before its work finishes. Joining creates an explicit lifecycle
boundary and propagates the thread result to its owner.

## Bad

```rust
fn start_report() {
    // Dropping the handle detaches the thread. Completion and panic are lost.
    std::thread::spawn(|| write_report());
}

fn write_report() -> Result<(), &'static str> { Ok(()) }
```

## Good

```rust
fn write_report() -> Result<(), &'static str> { Ok(()) }

fn run_report() -> Result<(), &'static str> {
    let handle = std::thread::spawn(write_report);
    handle.join().map_err(|_| "report worker panicked")??;
    Ok(())
}
```

For async tasks, await task handles and use structured cancellation instead of
detaching work.

## See Also

- [conc-scoped-threads](./conc-scoped-threads.md) - borrow stack data safely across threads
- [async-joinset-structured](./async-joinset-structured.md) - manage async task lifecycles
- [async-cancellation-token](./async-cancellation-token.md) - cancel tasks gracefully

## Source

Distilled from [Sharp Edges In The Rust Standard Library](https://corrode.dev/blog/sharp-edges-in-rust-std/).

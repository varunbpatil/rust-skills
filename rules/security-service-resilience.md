# security-service-resilience

> Design service failure handling around bounded, observable, graceful degradation

## Why It Matters

Production failures are normal: dependencies become slow, workers are restarted,
and traffic spikes. A service should define health/readiness signals, stop
accepting new work during shutdown, drain or cancel in-flight work deliberately,
and avoid amplifying a failed dependency with unlimited retries.

Use bounded retries with backoff and jitter. Apply circuit breakers or bulkheads
when a dependency's failures could consume all shared capacity. These controls
are operational policy, so select thresholds from measured service behavior and
test failure paths, not just successful requests.

## Bad

```rust
fn retry_forever<T, E>(mut operation: impl FnMut() -> Result<T, E>) -> T {
    loop {
        if let Ok(value) = operation() {
            return value;
        }
    }
}
```

## Good

### Bound Retries

```rust
fn retry_three_times<T, E>(mut operation: impl FnMut() -> Result<T, E>) -> Result<T, E> {
    let mut last = None;
    for _ in 0..3 {
        match operation() {
            Ok(value) => return Ok(value),
            Err(error) => last = Some(error),
        }
    }
    Err(last.expect("the loop always records a failure"))
}
```

In a real service, wait with bounded exponential backoff and jitter between
attempts, retry only errors known to be transient, and stop retries when the
request deadline or cancellation signal fires. A circuit breaker should reject
new calls for a short, observable period after repeated dependency failures.

## Ecosystem Building Blocks

[`tower`](https://crates.io/crates/tower) provides composable middleware for
timeouts, concurrency limits, load shedding, buffering, and retry policies for
services built around its `Service` abstraction. [`backon`](https://crates.io/crates/backon)
provides sync and async retry with configurable backoff and jitter when adopting
`tower` would be excessive. In either case, classify retryable errors, cap total
attempts and elapsed time, propagate cancellation, and ensure the operation is
safe to repeat. These libraries do not choose sound policy thresholds for the
application.

## See Also

- [async-cancellation-token](./async-cancellation-token.md) - coordinate graceful shutdown
- [async-bounded-channel](./async-bounded-channel.md) - preserve capacity with backpressure
- [security-resource-limits](./security-resource-limits.md) - bound external waits and work
- [obs-levels-filter](./obs-levels-filter.md) - make operational signals actionable
- [security-filesystem-boundaries](./security-filesystem-boundaries.md) - treat external boundaries as adversarial

## Source

Distilled from [Hardening Rust Code For Production](https://corrode.dev/blog/hardening-rust/).

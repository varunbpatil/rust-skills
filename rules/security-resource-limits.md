# security-resource-limits

> Bound untrusted work, memory, concurrency, and external waits at system boundaries

## Why It Matters

Safe Rust prevents memory unsafety, not resource exhaustion. An unbounded body,
queue, decompression stream, retry loop, or database call can still exhaust
memory, CPU, file descriptors, or workers. Set explicit request-size, queue,
concurrency, retry, and timeout limits at each boundary; choose values from the
service's workload and expose saturation in metrics.

Do not treat a timeout as cancellation by itself: ensure the underlying work can
be cancelled, dropped safely, or isolated from scarce shared resources.

## Bad

```rust
fn accept_everything(body: Vec<u8>) -> Vec<u8> {
    body // an untrusted caller controls this allocation
}
```

## Good

### Make Limits Executable

```rust
const MAX_REQUEST_BYTES: usize = 1_048_576;

fn accept_body(body: Vec<u8>) -> Result<Vec<u8>, &'static str> {
    if body.len() > MAX_REQUEST_BYTES {
        return Err("request body exceeds limit");
    }
    Ok(body)
}
```

For asynchronous dependencies, pair a timeout with a bounded queue and a
cancellation-safe operation. For example, `tokio::time::timeout` bounds waiting
for a request, while `tokio::sync::mpsc::channel(capacity)` bounds queued work.
Handle timeout and closed-channel errors explicitly; neither is a successful
response.

For per-client or global request-rate policy, the maintained
[`governor`](https://crates.io/crates/governor) crate implements token-bucket
rate limiting with direct and keyed limiters. A rate limiter complements body,
queue, concurrency, and deadline limits; it does not bound the cost of an
individual admitted request. Decide deliberately how keys expire so an
attacker cannot turn limiter state into another unbounded collection.

## See Also

- [async-bounded-channel](./async-bounded-channel.md) - apply backpressure with bounded queues
- [async-cancellation-token](./async-cancellation-token.md) - stop work gracefully
- [obs-structured-fields](./obs-structured-fields.md) - record useful saturation context
- [security-service-resilience](./security-service-resilience.md) - bound retries and degradation

## Source

Distilled from [Hardening Rust Code For Production](https://corrode.dev/blog/hardening-rust/).

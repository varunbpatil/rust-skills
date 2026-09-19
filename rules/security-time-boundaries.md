# security-time-boundaries

> Distinguish monotonic durations from civil time and treat platform clocks as fallible inputs

## Why It Matters

Wall clocks can move backward or jump forward because of synchronization,
manual adjustment, suspend/resume behavior, or virtualization. Local civil time
also depends on operating-system timezone data and contains ambiguous or
nonexistent instants around daylight-saving transitions. Code that treats time
as a steadily increasing integer works in tests and then fails at platform or
calendar boundaries.

Use [`std::time::Instant`] for elapsed durations and deadlines within one
process. Use [`std::time::SystemTime`] for timestamps that must relate to the
system clock, and handle its fallible arithmetic. For civil schedules, retain
the intended timezone identifier and use a timezone-aware library; a fixed UTC
offset does not encode future daylight-saving transitions.

## Bad

```rust
use std::time::{Duration, SystemTime};

fn elapsed_since(start: SystemTime) -> Duration {
    // The wall clock may have moved backward.
    SystemTime::now().duration_since(start).unwrap()
}
```

## Good

```rust
use std::time::{Duration, Instant, SystemTime, SystemTimeError};

fn elapsed_since(start: Instant) -> Duration {
    start.elapsed()
}

fn wall_clock_age(start: SystemTime) -> Result<Duration, SystemTimeError> {
    SystemTime::now().duration_since(start)
}
```

Do not persist an `Instant` or compare instants created by different processes;
it is process-local and has no civil-time meaning. In tests, inject a clock or
advance the async runtime's test clock instead of waiting on real time.

## Ecosystem Choice

Use [`jiff`](https://crates.io/crates/jiff) when the application needs civil
dates, timezone identifiers, timezone database transitions, or parsing and
formatting beyond the standard library's timestamp primitives. It distinguishes
absolute, civil, and zoned time in its API. Existing protocol or database
integrations may make `time` or `chrono` the more practical choice; enable only
the features the application uses and preserve timezone identifiers when future
civil-time behavior matters.

## See Also

- [async-select-racing](./async-select-racing.md) - combine deadlines with cancellation-safe work
- [test-tokio-async](./test-tokio-async.md) - control Tokio time in tests
- [num-overflow-explicit](./num-overflow-explicit.md) - handle arithmetic boundaries explicitly

## Source

Distilled from [Sharp Edges In The Rust Standard Library](https://corrode.dev/blog/sharp-edges-in-rust-std/).

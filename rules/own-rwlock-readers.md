# own-rwlock-readers

> Use `RwLock<T>` when reads significantly outnumber writes

## Why It Matters

`Mutex<T>` allows only one thread to access data at a time, even for reads.
`RwLock<T>` allows multiple concurrent readers or one exclusive writer. For
read-heavy workloads with sufficiently long critical sections, this can improve
throughput. Reader bookkeeping, cache-line contention, scheduling policy, and
short critical sections can also make an `RwLock` slower than a `Mutex`, so
benchmark the actual access pattern.

## Bad

```rust
use std::sync::{Arc, Mutex};

// Configuration rarely changes but is read constantly
let config = Arc::new(Mutex::new(Config::load()));

// Every read blocks other reads unnecessarily
fn get_setting(config: &Mutex<Config>, key: &str) -> String {
    let guard = config.lock().unwrap();
    guard.get(key).to_string()
}

// 100 threads reading = serialized, one at a time
```

## Good

```rust
use std::sync::{Arc, RwLock};

// Multiple readers can proceed concurrently
let config = Arc::new(RwLock::new(Config::load()));

fn get_setting(config: &RwLock<Config>, key: &str) -> String {
    let guard = config.read().unwrap(); // Multiple threads can hold read lock
    guard.get(key).to_string()
}

fn update_setting(config: &RwLock<Config>, key: &str, value: &str) {
    let mut guard = config.write().unwrap(); // Exclusive access for writes
    guard.set(key, value);
}

// 100 threads reading = parallel execution
```

## parking_lot::RwLock

Consider `parking_lot::RwLock` when its smaller locks, non-poisoning API,
upgradeable guards, or fairness controls fit the application. Benchmark it
against the standard lock under the target contention pattern:

```rust
use parking_lot::RwLock;
use std::sync::Arc;

let data = Arc::new(RwLock::new(HashMap::new()));

// Read - no unwrap needed
let value = data.read().get("key").cloned();

// Write
data.write().insert("key".to_string(), "value".to_string());

// Upgradeable read lock (unique to parking_lot)
let upgradeable = data.upgradable_read();
if upgradeable.get("key").is_none() {
    let mut write = parking_lot::RwLockUpgradableReadGuard::upgrade(upgradeable);
    write.insert("key".to_string(), "default".to_string());
}
```

## When RwLock Hurts

RwLock has overhead for tracking readers. It can be slower than Mutex when:

| Scenario                               | Better Choice            |
| -------------------------------------- | ------------------------ |
| Writes contend frequently with readers | Benchmark; often `Mutex` |
| Lock held very briefly                 | `Mutex`                  |
| Single-threaded                        | `RefCell`                |
| Reads dominate, lock held longer       | `RwLock`                 |

## Write Starvation

The standard lock's priority policy is platform-dependent. `parking_lot` uses
eventual fairness and also offers explicit fair unlock operations; neither
choice removes the need to evaluate latency under the target workload.

```rust
// parking_lot provides eventual fairness and explicit `unlock_fair` APIs.
use parking_lot::RwLock;

// `std` can atomically downgrade a write guard to a read guard (stable since
// Rust 1.92), preventing another writer from intervening during that
// transition. Downgrading is not a general fairness guarantee.
use std::sync::{RwLock as StdRwLock, RwLockWriteGuard};

let lock = StdRwLock::new(1);
let write = lock.write().expect("lock should not be poisoned");
let read = RwLockWriteGuard::downgrade(write);
assert_eq!(*read, 1);
```

## Immutable Snapshots

When readers only need the current immutable value and writers replace the
whole snapshot, [`arc-swap`](https://crates.io/crates/arc-swap) can avoid a read
lock. Readers cheaply load an `Arc<T>` while writers atomically publish another
one. It does not replace an `RwLock` for in-place mutation or invariants spanning
several independently updated values, and retained reader guards can delay
reclamation of older snapshots.

## Real-World Pattern: Cached Computation

```rust
use parking_lot::RwLock;
use std::sync::Arc;

struct CachedData {
    cache: RwLock<Option<ExpensiveResult>>,
}

impl CachedData {
    fn get(&self) -> ExpensiveResult {
        // Fast path: read lock
        if let Some(cached) = self.cache.read().as_ref() {
            return cached.clone();
        }

        // Slow path: compute and cache
        let result = compute_expensive();
        *self.cache.write() = Some(result.clone());
        result
    }
}
```

## See Also

- [own-mutex-interior](./own-mutex-interior.md) - When writes are frequent
- [async-no-lock-await](./async-no-lock-await.md) - RwLock in async contexts

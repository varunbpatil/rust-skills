# async-clone-before-await

> Own data needed across suspension; clone `Arc` when sharing ownership is required

## Why It Matters

References held across `.await` points become part of the future and can create
lifetime or `Send` constraints. Own or clone only what must outlive the current
poll. Cloning an `Arc<T>` can provide shared ownership cheaply, but the future is
`Send` only when every value held across suspension is `Send`; `Rc<T>` is not
`Send` and is suitable only for local tasks or single-threaded use.

## Bad

```rust
use std::sync::Arc;

async fn process(data: Arc<Data>) {
    // This borrow extends across await. Whether the future is Send depends on
    // the referenced types; the longer lifetime may still be inconvenient.
    let slice = &data.items[..];  // Borrow of Arc contents

    expensive_async_operation().await;  // Await with active borrow

    use_slice(slice);  // Still using the borrow
}

// This is rejected only if the captured values fail tokio::spawn's Send +
// 'static requirements; a shared slice is Send when Item: Sync.
tokio::spawn(process(data));
```

## Good

```rust
use std::sync::Arc;

async fn process(data: Arc<Data>) {
    // Clone what you need before await
    let items = data.items.clone();  // Owned Vec

    expensive_async_operation().await;

    use_items(&items);  // Using owned data
}

// Or clone the Arc itself
async fn share_data(data: Arc<Data>) {
    let data = data.clone();  // Another Arc handle

    some_async_work().await;

    process(&data);  // Safe - we own the Arc
}
```

## The Send Problem

```rust
// Futures must be Send to spawn on multi-threaded runtime
async fn not_send() {
    let rc = Rc::new(42);  // Rc is !Send

    tokio::time::sleep(Duration::from_secs(1)).await;

    println!("{}", rc);  // rc held across await
}

tokio::spawn(not_send());  // ERROR: future is not Send

// Fix: use Arc or don't hold across await
async fn is_send() {
    let arc = Arc::new(42);  // Arc is Send

    tokio::time::sleep(Duration::from_secs(1)).await;

    println!("{}", arc);
}

tokio::spawn(is_send());  // OK
```

## Minimizing Clones

```rust
// Bad: clone everything eagerly
async fn wasteful(data: Arc<LargeData>) {
    let data = (*data).clone();  // Clones entire LargeData
    async_work().await;
    use_one_field(&data.small_field);
}

// Good: clone only what you need
async fn efficient(data: Arc<LargeData>) {
    let small = data.small_field.clone();  // Clone only needed field
    async_work().await;
    use_one_field(&small);
}

// Good: if you need the whole thing, keep the Arc
async fn arc_efficient(data: Arc<LargeData>) {
    let data = data.clone();  // Cheap Arc clone
    async_work().await;
    use_data(&data);  // Access through Arc
}
```

## Spawn Pattern

```rust
// Common pattern: clone for spawned task
let shared = Arc::new(SharedState::new());

for i in 0..10 {
    let shared = shared.clone();  // Clone before moving into spawn
    tokio::spawn(async move {
        // Task owns its Arc clone
        shared.do_something(i).await;
    });
}
```

## Scope-Based Approach

```rust
// Limit borrow scope to before await
async fn scoped(data: Arc<Data>) {
    // Scope 1: borrow, compute, drop borrow
    let computed = {
        let slice = &data.items[..];  // Borrow
        compute_something(slice)       // Use
    };  // Borrow ends here

    // Now safe to await
    expensive_async_operation().await;

    use_computed(computed);
}
```

## MutexGuard Across Await

```rust
use tokio::sync::Mutex;

// BAD: holding guard across await
async fn bad(mutex: Arc<Mutex<Data>>) {
    let mut guard = mutex.lock().await;
    guard.value += 1;

    slow_operation().await;  // Guard held during await!

    guard.value += 1;
}

// GOOD: release before await
async fn good(mutex: Arc<Mutex<Data>>) {
    {
        let mut guard = mutex.lock().await;
        guard.value += 1;
    }  // Guard released

    slow_operation().await;

    {
        let mut guard = mutex.lock().await;
        guard.value += 1;
    }
}
```

## See Also

- [async-no-lock-await](./async-no-lock-await.md) - Lock guards across await
- [own-arc-shared](./own-arc-shared.md) - Arc usage patterns
- [async-spawn-blocking](./async-spawn-blocking.md) - Blocking in async

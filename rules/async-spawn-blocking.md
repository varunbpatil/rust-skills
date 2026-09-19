# async-spawn-blocking

> Offload blocking work; bound or separately pool sustained CPU work

## Why It Matters

Async runtimes like Tokio use a small number of threads to handle many tasks.
CPU-intensive or blocking operations on these threads starve other tasks.
`spawn_blocking` moves synchronous work to Tokio's blocking pool. Because that
pool permits many threads by default and a running blocking task cannot be
aborted, bound admission for CPU work or use a dedicated CPU pool such as Rayon.

## Bad

```rust
// BAD: Blocks the async runtime thread
async fn process_image(data: &[u8]) -> ProcessedImage {
    // CPU-intensive work on async thread!
    let resized = resize_image(data);      // Blocks!
    let compressed = compress(resized);     // Blocks!
    compressed
}

// BAD: Synchronous file I/O in async context
async fn read_large_file(path: &Path) -> Vec<u8> {
    std::fs::read(path).unwrap()  // Blocks the runtime!
}
```

## Good

```rust
use tokio::task;

// GOOD: Offload CPU work to blocking pool
async fn process_image(data: Vec<u8>) -> ProcessedImage {
    task::spawn_blocking(move || {
        let resized = resize_image(&data);
        compress(resized)
    })
    .await
    .expect("spawn_blocking failed")
}

// GOOD: Use async file I/O
async fn read_large_file(path: &Path) -> tokio::io::Result<Vec<u8>> {
    tokio::fs::read(path).await
}

// GOOD: Or spawn_blocking for unavoidable sync I/O
async fn read_with_sync_lib(path: PathBuf) -> Vec<u8> {
    task::spawn_blocking(move || {
        sync_library::read_file(&path)
    })
    .await
    .unwrap()
}
```

## What Counts as Blocking

```rust,ignore
// CPU-intensive operations
- Cryptographic operations (hashing, encryption)
- Image/video processing
- Compression/decompression
- Complex parsing
- Mathematical computations

// Blocking I/O
- std::fs operations
- Synchronous database drivers
- Synchronous HTTP clients
- Thread::sleep

// There is no portable duration threshold. Measure tail latency under the
// target runtime configuration and workload. Bound expensive work so bursts
// cannot create an unbounded queue or too many active blocking tasks.
```

## Practical Examples

```rust
use std::io::Write as _;

// Password hashing (CPU-intensive)
async fn hash_password(password: String) -> anyhow::Result<String> {
    Ok(task::spawn_blocking(move || {
        bcrypt::hash(password, bcrypt::DEFAULT_COST)
    })
    .await??)
}

// JSON parsing of large documents
async fn parse_large_json(data: String) -> anyhow::Result<serde_json::Value> {
    Ok(task::spawn_blocking(move || serde_json::from_str(&data)).await??)
}

// Compression
async fn compress_data(data: Vec<u8>) -> anyhow::Result<Vec<u8>> {
    Ok(task::spawn_blocking(move || -> std::io::Result<Vec<u8>> {
        let mut encoder = flate2::write::GzEncoder::new(
            Vec::new(),
            flate2::Compression::default(),
        );
        encoder.write_all(&data)?;
        encoder.finish()
    })
    .await??)
}
```

## spawn_blocking vs spawn

```rust
// spawn: Runs async code on runtime threads
tokio::spawn(async {
    // Async code here
    some_async_operation().await;
});

// spawn_blocking: Runs sync code on blocking thread pool
tokio::task::spawn_blocking(|| {
    // Synchronous, possibly CPU-intensive code
    heavy_computation();
});

// spawn_blocking returns JoinHandle that can be awaited
let result = tokio::task::spawn_blocking(|| {
    expensive_sync_operation()
}).await?;
```

## Rayon for Parallel CPU Work

```rust
// For sustained parallel CPU work, use a bounded Rayon pool. The outer
// spawn_blocking bridge prevents waiting for Rayon from occupying an executor
// worker; do not create a new Rayon pool per request.
async fn parallel_process(items: Vec<Item>) -> Vec<Output> {
    task::spawn_blocking(move || {
        use rayon::prelude::*;
        items.par_iter()
            .map(|item| cpu_intensive_transform(item))
            .collect()
    })
    .await
    .unwrap()
}
```

## See Also

- [async-tokio-fs](async-tokio-fs.md) - Use tokio::fs for async file I/O
- [async-no-lock-await](async-no-lock-await.md) - Don't hold locks across await
- [security-resource-limits](security-resource-limits.md) - Bound concurrency and work at trust boundaries

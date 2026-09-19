# async-tokio-fs

> Keep potentially slow filesystem operations off async executor threads

## Why It Matters

`std::fs` operations are blocking—they stop the current thread until the syscall
completes. In latency-sensitive async code, use `tokio::fs` or an explicitly
managed blocking pool to keep executor workers responsive. Tokio filesystem
operations are not kernel-level asynchronous on the common platforms: they use
blocking threads, so concurrency still needs a bound. Synchronous access can be
reasonable during startup or when measurement establishes that the operation is
short and infrequent.

## Bad

```rust
async fn process_files(paths: &[PathBuf]) -> Result<Vec<String>> {
    let mut contents = Vec::new();

    for path in paths {
        // BLOCKS the entire executor thread!
        let data = std::fs::read_to_string(path)?;
        contents.push(data);
    }

    Ok(contents)
}

// While reading a file, NO other tasks can run on this thread
```

## Good

```rust,ignore
use tokio::fs;

async fn process_files(paths: &[PathBuf]) -> Result<Vec<String>> {
    let mut contents = Vec::new();

    for path in paths {
        // Non-blocking: allows other tasks to run
        let data = fs::read_to_string(path).await?;
        contents.push(data);
    }

    Ok(contents)
}

// For independent reads, use bounded concurrency rather than spawning one
// blocking operation for every untrusted path at once.
async fn process_files_concurrent(paths: &[PathBuf]) -> Result<Vec<String>> {
    use futures::{stream, StreamExt, TryStreamExt};

    stream::iter(paths)
        .map(|path| fs::read_to_string(path))
        .buffered(16)
        .try_collect()
}
```

## tokio::fs API

```rust
use tokio::fs;

// Reading
let contents = fs::read_to_string("file.txt").await?;
let bytes = fs::read("file.bin").await?;

// Writing
fs::write("output.txt", "contents").await?;

// File operations
let file = fs::File::open("file.txt").await?;
let file = fs::File::create("new.txt").await?;

// Directory operations
fs::create_dir("new_dir").await?;
fs::create_dir_all("nested/dir/path").await?;
fs::remove_dir("empty_dir").await?;
fs::remove_dir_all("dir_with_contents").await?;

// Metadata
let metadata = fs::metadata("file.txt").await?;
let canonical = fs::canonicalize("./relative").await?;

// Rename/remove
fs::rename("old.txt", "new.txt").await?;
fs::remove_file("file.txt").await?;

// Read directory
let mut entries = fs::read_dir("some_dir").await?;
while let Some(entry) = entries.next_entry().await? {
    println!("{}", entry.path().display());
}
```

## Async File I/O

```rust
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt, AsyncBufReadExt, BufReader};

// Read with buffer
let mut file = File::open("large.bin").await?;
let mut buffer = vec![0u8; 4096];
let bytes_read = file.read(&mut buffer).await?;

// Read all
let mut contents = Vec::new();
file.read_to_end(&mut contents).await?;

// Write
let mut file = File::create("output.bin").await?;
file.write_all(b"data").await?;
file.flush().await?;

// Buffered line reading
let file = File::open("lines.txt").await?;
let reader = BufReader::new(file);
let mut lines = reader.lines();

while let Some(line) = lines.next_line().await? {
    println!("{}", line);
}
```

## When std::fs is Acceptable

```rust,ignore
// Startup/initialization (before async runtime)
fn main() {
    let config = std::fs::read_to_string("config.toml")
        .expect("config file required");

    tokio::runtime::Runtime::new()
        .unwrap()
        .block_on(run_with_config(config));
}

// Do not block a current-thread runtime: it prevents every other task there
// from making progress.
#[tokio::main(flavor = "current_thread")]
async fn main() {
    // Use tokio::fs or move synchronous work off this executor thread.
}

// When file operations are rare and quick
// (e.g., reading small config once per hour)
```

## Performance Considerations

```rust
// tokio::fs uses spawn_blocking internally
// For many small files, the overhead adds up

// Bound concurrent operations; batching alone does not bound try_join_all.
let paths: Vec<_> = entries.iter()
    .map(|e| e.path())
    .collect();

let contents: Vec<_> = futures::stream::iter(paths)
    .map(|p| fs::read_to_string(p))
    .buffered(16)
    .try_collect()
    .await?;

// For heavy I/O, consider memory-mapped files
// (requires unsafe or mmap crate)
```

## See Also

- [async-spawn-blocking](./async-spawn-blocking.md) - How tokio::fs works internally
- [async-tokio-runtime](./async-tokio-runtime.md) - Runtime configuration
- [err-context-chain](./err-context-chain.md) - Adding path context to IO errors
- [security-resource-limits](./security-resource-limits.md) - Bound externally driven concurrency

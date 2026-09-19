# err-anyhow-app

> Use `anyhow` for application error handling

## Why It Matters

At an application boundary, binaries often do not need typed errors — they need to report failures with good context. `anyhow` provides context chaining, backtraces, and conversion from many error types. Keep typed domain, port-contract, and use-case errors below that boundary: a service must not expose raw `anyhow::Error` as its business contract.

Use `anyhow` in binary entry points, startup/configuration, CLI orchestration, and top-level error reporting. An outbound adapter first maps vendor failures to an application-owned port error; a service may map that again to a use-case error; the binary can then add context and report it with `anyhow`.

## Bad

```rust
// Tedious type management
fn load_config() -> Result<Config, Box<dyn std::error::Error>> {
    let path = find_config()?;  // Returns FindError
    let content = std::fs::read_to_string(&path)?;  // Returns io::Error
    let config: Config = toml::from_str(&content)?;  // Returns toml::Error
    validate(&config)?;  // Returns ValidationError
    Ok(config)
}

// No context - hard to debug
fn process() -> Result<(), Box<dyn std::error::Error>> {
    let data = fetch()?;  // Which fetch failed?
    transform(data)?;     // What was being transformed?
    save()?;              // Where was it saving to?
    Ok(())
}
```

## Good

```rust
use anyhow::{Context, Result};

fn load_config() -> Result<Config> {
    let path = find_config()
        .context("failed to locate config file")?;

    let content = std::fs::read_to_string(&path)
        .with_context(|| format!("failed to read config from {}", path.display()))?;

    let config: Config = toml::from_str(&content)
        .context("failed to parse config as TOML")?;

    validate(&config)
        .context("config validation failed")?;

    Ok(config)
}

// Error message: "config validation failed: field 'port' must be > 0"
// Full chain preserved for debugging
```

## Key Features

```rust
use anyhow::{anyhow, bail, ensure, Context, Result};

fn example() -> Result<()> {
    // Create ad-hoc errors
    let err = anyhow!("something went wrong");

    // Early return with error
    bail!("aborting due to {}", reason);

    // Assert with error
    ensure!(condition, "condition was false");

    // Add context to any error
    risky_operation()
        .context("risky operation failed")?;

    // Dynamic context
    fetch(url)
        .with_context(|| format!("failed to fetch {}", url))?;

    Ok(())
}
```

## Main Function Pattern

```rust,ignore
use anyhow::Result;

fn main() -> Result<()> {
    let config = load_config()?;
    run_app(config)?;
    Ok(())
}

// Or with custom exit handling
fn main() {
    if let Err(e) = run() {
        eprintln!("Error: {:#}", e);  // Pretty-print with causes
        std::process::exit(1);
    }
}

fn run() -> Result<()> {
    // Application logic
    Ok(())
}
```

## Error Display Formats

```rust
use anyhow::Result;

fn show_error(err: anyhow::Error) {
    // Just the top-level message
    println!("{}", err);
    // "config validation failed"

    // With cause chain (# alternate format)
    println!("{:#}", err);
    // "config validation failed: field 'port' must be > 0"

    // Debug format with backtrace
    println!("{:?}", err);
    // Full backtrace if RUST_BACKTRACE=1

    // Iterate through cause chain
    for cause in err.chain() {
        println!("Caused by: {}", cause);
    }
}
```

## Combining with thiserror

```rust
// In your library crate - typed errors
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ApiError {
    #[error("rate limited")]
    RateLimited,
    #[error("not found: {0}")]
    NotFound(String),
}

// In your application - anyhow for handling
use anyhow::{Context, Result};

fn fetch_user(id: u64) -> Result<User> {
    api::get_user(id)
        .with_context(|| format!("failed to fetch user {}", id))
}

// Can still downcast if needed
fn handle_error(err: anyhow::Error) {
    if let Some(api_err) = err.downcast_ref::<ApiError>() {
        match api_err {
            ApiError::RateLimited => wait_and_retry(),
            ApiError::NotFound(id) => log_missing(id),
        }
    }
}
```

## When to Use Which

| Situation                                         | Use                           |
| ------------------------------------------------- | ----------------------------- |
| Library public API                                | `thiserror`                   |
| Binary entry point, startup, or CLI orchestration | `anyhow`                      |
| Domain, port, or use-case contract                | Typed application-owned error |
| CLI tools                                         | `anyhow`                      |
| Internal library code                             | Either                        |
| Need to match error variants                      | `thiserror`                   |
| Just need to report errors                        | `anyhow`                      |

## Rich User-Facing Diagnostics

[`miette`](https://crates.io/crates/miette) is a good presentation layer for
CLI or developer tools that need source spans, labels, error codes, help text,
and graphical reports. Keep domain and library errors typed; convert them into
diagnostic reports at the application boundary. `anyhow` remains simpler when a
contextual cause chain is sufficient.

## See Also

- [err-thiserror-lib](err-thiserror-lib.md) - Use thiserror for libraries
- [err-context-chain](err-context-chain.md) - Add context to errors
- [proj-ports-adapters](proj-ports-adapters.md) - keep port and use-case error contracts typed

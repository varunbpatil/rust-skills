# err-from-impl

> Implement `From<E>` for error conversions to enable `?` operator

## Why It Matters

The `?` operator automatically converts errors using `From` trait. By implementing `From<SourceError> for YourError`, you enable seamless error propagation without explicit `.map_err()` calls. This makes error handling code cleaner and ensures consistent error wrapping throughout your codebase.

Use direct `From<vendor::Error>` conversions only in code that owns the vendor dependency, such as an adapter or startup/configuration layer. Do not let that conversion make a driver error part of an outbound-port or use-case error contract; map it to an application-owned port-specific error at the adapter boundary instead.

## Bad

```rust
#[derive(Debug)]
enum AdapterError {
    Io(std::io::Error),
    Parse(serde_json::Error),
    Database(diesel::result::Error),
}

fn load_config(path: &str) -> Result<Config, AdapterError> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| AdapterError::Io(e))?;  // Manual conversion everywhere

    let config: Config = serde_json::from_str(&content)
        .map_err(|e| AdapterError::Parse(e))?;  // Repeated boilerplate

    save_to_db(&config)
        .map_err(|e| AdapterError::Database(e))?;  // Gets tedious

    Ok(config)
}
```

## Good

```rust
#[derive(Debug)]
enum AdapterError {
    Io(std::io::Error),
    Parse(serde_json::Error),
    Database(diesel::result::Error),
}

// Implement From for each source error type
impl From<std::io::Error> for AdapterError {
    fn from(err: std::io::Error) -> Self {
        AdapterError::Io(err)
    }
}

impl From<serde_json::Error> for AdapterError {
    fn from(err: serde_json::Error) -> Self {
        AdapterError::Parse(err)
    }
}

impl From<diesel::result::Error> for AdapterError {
    fn from(err: diesel::result::Error) -> Self {
        AdapterError::Database(err)
    }
}

fn load_config(path: &str) -> Result<Config, AdapterError> {
    let content = std::fs::read_to_string(path)?;  // Auto-converts
    let config: Config = serde_json::from_str(&content)?;  // Clean!
    save_to_db(&config)?;
    Ok(config)
}
```

## Use thiserror for Automatic From

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum AdapterError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),  // Auto-generates From impl

    #[error("Parse error: {0}")]
    Parse(#[from] serde_json::Error),  // #[from] does the work

    #[error("Database error: {0}")]
    Database(#[from] diesel::result::Error),
}

// Now ? just works
fn load_config(path: &str) -> Result<Config, AdapterError> {
    let content = std::fs::read_to_string(path)?;
    let config: Config = serde_json::from_str(&content)?;
    save_to_db(&config)?;
    Ok(config)
}
```

## From with Context

Sometimes you need to add context during conversion:

```rust,ignore
#[derive(Error, Debug)]
enum ConfigError {
    #[error("Failed to read config from '{path}': {source}")]
    ReadFailed {
        path: String,
        #[source]
        source: std::io::Error,
    },
}

// Can't use #[from] when you need extra context
fn load_config(path: &str) -> Result<Config, ConfigError> {
    let content = std::fs::read_to_string(path)
        .map_err(|source| ConfigError::ReadFailed {
            path: path.to_string(),
            source,
        })?;
    // ...
}

// Or use anyhow for ad-hoc context
use anyhow::{Context, Result};

fn load_config(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read config from '{}'", path))?;
    // ...
}
```

## Blanket From Implementations

Be careful with blanket implementations:

```rust,ignore
// ❌ Too broad - conflicts with other From impls
impl<E: std::error::Error> From<E> for AdapterError {
    fn from(err: E) -> Self {
        AdapterError::Other(err.to_string())
    }
}

// ✅ Specific implementations
impl From<std::io::Error> for AdapterError { ... }
impl From<ParseIntError> for AdapterError { ... }
```

## See Also

- [err-thiserror-lib](./err-thiserror-lib.md) - Using thiserror for libraries
- [err-source-chain](./err-source-chain.md) - Preserving error chains
- [err-question-mark](./err-question-mark.md) - The ? operator
- [conv-tryfrom-fallible](./conv-tryfrom-fallible.md) - TryFrom for fallible conversions
- [proj-ports-adapters](./proj-ports-adapters.md) - translate vendor errors at adapter boundaries

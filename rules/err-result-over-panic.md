# err-result-over-panic

> Return `Result<T, E>` instead of panicking for recoverable errors

## Why It Matters

A panic either unwinds the current thread or aborts the process, according to
the panic strategy and boundary involved. Although unwind panics can sometimes
be caught with `catch_unwind`, they are not ordinary typed error handling.
`Result<T, E>` lets callers retry, fall back, propagate, or report expected
failures. Public APIs should reserve panics for documented precondition
violations and bugs rather than malformed input or environmental failures.

## Bad

```rust
fn parse_config(path: &str) -> Config {
    let content = std::fs::read_to_string(path)
        .expect("Failed to read config");  // Crashes on missing file

    serde_json::from_str(&content)
        .expect("Invalid config format")   // Crashes on bad JSON
}

fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        panic!("Division by zero!");  // Crashes the program
    }
    a / b
}
```

Caller has no chance to recover or provide a fallback.

## Good

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum ConfigError {
    #[error("failed to read config file: {0}")]
    Io(#[from] std::io::Error),
    #[error("invalid config format: {0}")]
    Parse(#[from] serde_json::Error),
}

fn parse_config(path: &str) -> Result<Config, ConfigError> {
    let content = std::fs::read_to_string(path)?;
    let config = serde_json::from_str(&content)?;
    Ok(config)
}

fn divide(a: i32, b: i32) -> Result<i32, &'static str> {
    if b == 0 {
        return Err("Division by zero");
    }
    Ok(a / b)
}

// Caller decides how to handle
match parse_config("app.json") {
    Ok(config) => run_app(config),
    Err(e) => {
        eprintln!("Using default config: {}", e);
        run_app(Config::default())
    }
}
```

## When Panic IS Appropriate

```rust,ignore
// 1. Bug in the program (invariant violation)
fn get_cached_value(&self, key: &str) -> &Value {
    self.cache.get(key).expect("BUG: key was verified to exist")
}

// 2. Setup/initialization that can't reasonably fail
fn main() {
    let config = Config::load().expect("Failed to load required config");
    // Can't run without config, panic is reasonable
}

// 3. Tests
#[test]
fn test_parse() {
    let result = parse("valid input").unwrap(); // unwrap OK in tests
    assert_eq!(result, expected);
}

// 4. Examples and prototypes
fn main() {
    // Quick prototype, panic is fine
    let data = fetch_data().unwrap();
}
```

## Panic vs Result Decision Guide

| Situation                            | Use                        |
| ------------------------------------ | -------------------------- |
| File not found                       | `Result`                   |
| Network error                        | `Result`                   |
| Invalid user input                   | `Result`                   |
| Parse error                          | `Result`                   |
| Index out of bounds (from user data) | `Result`                   |
| Index out of bounds (internal bug)   | Panic                      |
| Violated internal invariant          | Panic                      |
| Unimplemented code path              | Panic (`unimplemented!()`) |
| Impossible state reached             | Panic (`unreachable!()`)   |

## Library vs Application

```rust
// Library: NEVER panic on user input
pub fn parse(input: &str) -> Result<Ast, ParseError> {
    // Always return Result
}

// Application: Can panic at top level for critical failures
fn main() {
    if let Err(e) = run() {
        eprintln!("Fatal error: {}", e);
        std::process::exit(1);
    }
}
```

## See Also

- [err-thiserror-lib](./err-thiserror-lib.md) - Define error types for libraries
- [err-anyhow-app](./err-anyhow-app.md) - Ergonomic errors for applications
- [err-no-unwrap-prod](./err-no-unwrap-prod.md) - Avoid unwrap in production code
- [anti-unwrap-abuse](./anti-unwrap-abuse.md) - When unwrap is acceptable

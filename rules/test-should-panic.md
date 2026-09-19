# test-should-panic

> Use `#[should_panic]` to test that code panics as expected

## Why It Matters

Some code should panic on invalid inputs or invariant violations. `#[should_panic]` verifies the panic occurs, optionally checking the panic message. This ensures defensive panics work correctly and documents expected panic conditions.

## Bad

```rust
#[test]
fn test_panic() {
    // Just calling panicking code makes test fail
    divide(1, 0);  // Test fails with panic
}

// Using catch_unwind is verbose
#[test]
fn test_panic_manual() {
    let result = std::panic::catch_unwind(|| divide(1, 0));
    assert!(result.is_err());
}
```

## Good

```rust
#[test]
#[should_panic]
fn divide_by_zero_panics() {
    divide(1, 0);  // Test passes when this panics
}

// With expected message
#[test]
#[should_panic(expected = "division by zero")]
fn divide_by_zero_panics_with_message() {
    divide(1, 0);  // Panics with "division by zero"
}

// Partial message match
#[test]
#[should_panic(expected = "index out of bounds")]
fn index_panic_contains_message() {
    let v = vec![1, 2, 3];
    let _ = v[100];  // Message contains "index out of bounds"
}
```

## Testing Internal Invariants

```rust
struct Parser {
    // Private parser construction establishes this invariant after tokenization.
    current_token: Option<String>,
}

impl Parser {
    fn current_token(&self) -> &str {
        self.current_token
            .as_deref()
            .expect("parser maintains a current token")
    }
}

#[test]
#[should_panic(expected = "parser maintains a current token")]
fn parser_invariant_violation_panics() {
    // Unit tests within the module may deliberately construct invalid private state.
    Parser { current_token: None }.current_token();
}

#[test]
fn parser_returns_its_current_token() {
    let parser = Parser { current_token: Some("name".into()) };
    assert_eq!(parser.current_token(), "name");
}
```

## With expect() Messages

```rust
fn get_config_value(key: &str) -> String {
    CONFIG.get(key)
        .expect(&format!("missing required config: {}", key))
        .to_string()
}

#[test]
#[should_panic(expected = "missing required config: DATABASE_URL")]
fn missing_config_panics_with_key() {
    get_config_value("DATABASE_URL");
}
```

## When NOT to Use should_panic

```rust
// ❌ For recoverable errors - use Result
#[test]
#[should_panic]  // Wrong: this should return Err, not panic
fn invalid_input_panics() {
    parse_config("invalid");  // Should return Err, not panic
}

// ✅ Return Result and test the error
#[test]
fn invalid_input_returns_error() {
    let result = parse_config("invalid");
    assert!(result.is_err());
}
```

## Combining with Result

```rust
#[test]
#[should_panic]
fn test_panics() -> Result<(), Error> {
    // Can combine with Result for setup
    let data = setup_test_data()?;

    // This should panic
    process_invalid(&data);

    Ok(())  // Never reached
}
```

## See Also

- [err-result-over-panic](./err-result-over-panic.md) - Panic vs Result
- [err-expect-bugs-only](./err-expect-bugs-only.md) - When to use expect
- [test-descriptive-names](./test-descriptive-names.md) - Test naming
- [type-nonempty-collection](./type-nonempty-collection.md) - model required non-empty input with fallible construction

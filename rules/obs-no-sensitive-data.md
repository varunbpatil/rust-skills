# obs-no-sensitive-data

> Never log secrets or PII; redact or skip them

## Why It Matters

Logs and traces are routinely shipped to cloud aggregators (Datadog, Grafana Loki, Splunk) and retained for weeks or months. If a password, API token, session cookie, or piece of PII (email, SSN, health data) appears in a log line or span field, it leaks into systems with weaker access controls than your secrets manager, appears in support exports, and may violate GDPR/HIPAA/PCI-DSS. Use `#[instrument(skip(...))]` or `skip_all` to exclude sensitive arguments, and wrap sensitive types in a redacting newtype or use the `secrecy` crate's `SecretString`/`SecretBox<T>`, whose `Debug` output is redacted and whose contents require explicit exposure.

## Bad

```rust
use tracing::instrument;

struct Credentials {
    username: String,
    password: String,   // secret
    api_key: String,    // secret
}

// BAD: instrument auto-captures all args as fields — password becomes a span field
#[instrument]
async fn authenticate(credentials: &Credentials) -> bool {
    // Also BAD: manual logging of the whole struct
    tracing::info!(?credentials, "authenticating user");
    true
}
```

## Good

```rust
use tracing::{info, instrument};

// A simple redacting newtype — implement for any sensitive type
#[derive(Clone)]
struct Secret(String);

impl std::fmt::Debug for Secret {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("[redacted]")
    }
}

impl std::fmt::Display for Secret {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("[redacted]")
    }
}

struct Credentials {
    username: String,
    password: Secret,   // redacts in Debug/Display
    api_key: Secret,    // redacts in Debug/Display
}

// GOOD: skip sensitive args by name
#[instrument(skip(credentials), fields(username = %credentials.username))]
async fn authenticate(credentials: &Credentials) -> bool {
    info!("authenticating user");
    // password and api_key never appear in any span field or log line
    verify_password(&credentials.username, &credentials.password)
}

fn verify_password(_username: &str, _password: &Secret) -> bool { true }
```

```rust
use secrecy::{ExposeSecret as _, SecretString};

let password = SecretString::from("correct horse battery staple");
assert_eq!(password.expose_secret(), "correct horse battery staple");

// `Debug` is redacted, and `SecretString` deliberately has no `Display` impl.
let diagnostic = format!("{password:?}");
assert!(!diagnostic.contains(password.expose_secret()));
```

## Key Points

- **`skip(arg)`**: exclude a single argument from `#[instrument]` auto-captured fields.
- **`skip_all`**: exclude all arguments; then add only safe fields with `fields(key = value)`.
- **Redacting newtypes**: override `Debug` and `Display` to emit `"[redacted]"` — this protects against accidental `?arg` or `%arg` elsewhere in the codebase.
- **`secrecy` crate**: provides `SecretString` and `SecretBox<T>` with redacted `Debug`, no generic `Display` implementation, explicit `.expose_secret()` access, and zeroization on drop for supported contents.
- **Do not log full request bodies** in production: they may contain tokens, credentials, or PII embedded in JSON payloads. Log only metadata (size, content-type, path).
- Audit existing spans with `RUST_LOG=trace` in a staging environment before shipping.

## See Also

- [obs-instrument-spans](obs-instrument-spans.md) - how to use `#[instrument]` and spans correctly
- [obs-structured-fields](obs-structured-fields.md) - structured fields must be safe to emit
- [err-thiserror-lib](err-thiserror-lib.md) - defining error types that don't accidentally expose secrets
- [security-secret-comparisons](security-secret-comparisons.md) - compare attacker-observable secrets safely

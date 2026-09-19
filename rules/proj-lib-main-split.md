# proj-lib-main-split

> Keep `main.rs` minimal, logic in `lib.rs`

## Why It Matters

Putting your logic in `lib.rs` makes it testable, reusable, and keeps `main.rs` as a thin entry point. Integration tests can only access your library crate, not binary code in `main.rs`.

## Bad

```rust
// src/main.rs - everything here
fn main() {
    let args = parse_args();
    let config = load_config(&args.config_path).unwrap();
    let db = connect_database(&config.db_url).unwrap();

    // Hundreds of lines of application logic...
    // All untestable from integration tests!
}

fn parse_args() -> Args { /* ... */ }
fn load_config(path: &str) -> Result<Config, Error> { /* ... */ }
fn connect_database(url: &str) -> Result<Db, Error> { /* ... */ }
// ... more functions that can't be tested
```

## Good

```rust
// src/main.rs - thin entry point
use my_app::{run, Config};

fn main() -> anyhow::Result<()> {
    let config = Config::from_env()?;
    run(config)
}

// src/lib.rs - application code; the binary calls this thin entry point
pub mod config;
mod user;

pub use config::Config;

pub fn run(config: Config) -> anyhow::Result<()> {
    // These are `pub(crate)` re-exports from `user`; the binary cannot name them.
    let repository = user::SqliteUserRepository::connect(&config.database_url)?;
    let service = user::UserService::new(repository);
    let app = user::router(service);
    app.run()
}
```

## With CLI Arguments

```rust
// src/main.rs
use clap::Parser;
use my_app::{run, Args};

fn main() -> anyhow::Result<()> {
    let args = Args::parse();
    run(args)
}

// src/lib.rs
use clap::Parser;

#[derive(Parser, Debug)]
#[command(name = "myapp", version, about)]
pub struct Args {
    #[arg(short, long)]
    pub config: PathBuf,

    #[arg(short, long, default_value = "info")]
    pub log_level: String,
}

pub fn run(args: Args) -> anyhow::Result<()> {
    // All application logic here - testable!
}
```

## Project Structure

```
my_app/
├── Cargo.toml
├── src/
│   ├── main.rs       # Thin entry point; invokes application startup
│   ├── lib.rs        # Library root and feature declarations
│   ├── config.rs     # Configuration
│   └── user/
│       ├── mod.rs
│       ├── models.rs
│       ├── errors.rs
│       ├── ports.rs
│       ├── service.rs
│       └── adapters/
│           ├── http.rs
│           └── sqlite.rs
└── tests/
    └── integration.rs  # Can access lib.rs!
```

`main.rs` remains the binary's process entry point. Keeping its work to parsing process input and invoking `run` makes it thin; `run` is the composition function and can assemble crate-private adapters without exposing them from the library API. The feature module re-exports the concrete adapter, service, and router as `pub(crate)`, and their constructors and functions must also be `pub(crate)`: a re-export cannot widen a private item. The router receives the concrete service through the inbound port it implements, so router tests can substitute a fake implementation of that inbound port without exposing the concrete service.

## Testing Benefits

```rust
// tests/integration.rs - can test everything!
use my_app::{Config, run};

#[test]
fn test_full_workflow() {
    let config = Config::test_config();
    // Test the actual run function
    assert!(my_app::run(config).is_ok());
}
```

## Multiple Binaries

```rust
// src/lib.rs - public startup functions; concrete wiring stays private
mod cli;
mod server;

pub fn run_server() -> anyhow::Result<()> {
    server::run()
}

pub fn run_cli() -> anyhow::Result<()> {
    cli::run()
}

// src/bin/server.rs
use my_app::run_server;

fn main() -> anyhow::Result<()> {
    run_server()
}

// src/bin/cli.rs
use my_app::run_cli;

fn main() -> anyhow::Result<()> {
    run_cli()
}
```

Each binary owns only process-specific setup and invokes its public library startup function. That function can assemble crate-private adapters and services without making infrastructure types part of the library API.

## See Also

- [proj-bin-dir](proj-bin-dir.md) - Put multiple binaries in src/bin/
- [proj-mod-by-feature](proj-mod-by-feature.md) - Organize modules by feature
- [test-integration-dir](test-integration-dir.md) - Integration tests in tests/

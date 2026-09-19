# test-mock-traits

> Use traits for dependencies to enable mocking in tests

## Why It Matters

Concrete dependencies make testing hard—you can't easily test error paths, timeouts, or edge cases without real external systems. Extracting dependencies behind traits lets you inject test doubles (mocks, fakes, stubs), enabling isolated unit tests that run fast and cover edge cases.

## Bad

```rust
struct UserService {
    db: PostgresConnection,  // Concrete type - hard to test
}

impl UserService {
    async fn get_user(&self, id: u64) -> Result<User, Error> {
        // Directly calls Postgres - needs real database to test
        self.db.query("SELECT * FROM users WHERE id = $1", &[&id]).await
    }
}

// Test requires real Postgres instance
#[tokio::test]
async fn test_get_user() {
    let db = PostgresConnection::connect("postgres://...").await?;
    let service = UserService { db };
    // Slow, flaky, can't test error paths
}
```

## Good

```rust
// Define trait for dependency
#[async_trait]
trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: u64) -> Result<Option<User>, UserRepositoryError>;
    async fn save(&self, user: &User) -> Result<(), UserRepositoryError>;
}

// Application-owned port error, never sqlx::Error or a database error code.
enum UserRepositoryError {
    Unavailable,
}

// Error exposed by this use case.
enum GetUserError {
    NotFound,
    Repository(UserRepositoryError),
}

// Production adapter: framework and SQL types stay here.
struct PostgresUserRepo {
    pool: PgPool,
}

#[async_trait]
impl UserRepository for PostgresUserRepo {
    async fn find_by_id(&self, id: u64) -> Result<Option<User>, UserRepositoryError> {
        sqlx::query_as("SELECT * FROM users WHERE id = $1")
            .bind(id)
            .fetch_optional(&self.pool)
            .await
            .map_err(|_| UserRepositoryError::Unavailable)
    }

    async fn save(&self, _user: &User) -> Result<(), UserRepositoryError> {
        todo!("the production adapter owns the SQL insert")
    }
}

// Service depends on trait, not concrete type
struct UserService<R: UserRepository> {
    repo: R,
}

impl<R: UserRepository> UserService<R> {
    async fn get_user(&self, id: u64) -> Result<User, GetUserError> {
        self.repo
            .find_by_id(id)
            .await
            .map_err(GetUserError::Repository)?
            .ok_or(GetUserError::NotFound)
    }
}

// Test with mock
#[cfg(test)]
mod tests {
    struct MockUserRepo {
        users: HashMap<u64, User>,
    }

    #[async_trait]
    impl UserRepository for MockUserRepo {
        async fn find_by_id(&self, id: u64) -> Result<Option<User>, UserRepositoryError> {
            Ok(self.users.get(&id).cloned())
        }

        async fn save(&self, _user: &User) -> Result<(), UserRepositoryError> {
            Ok(())
        }
    }

    #[tokio::test]
    async fn test_get_user_found() {
        let mut mock = MockUserRepo { users: HashMap::new() };
        mock.users.insert(1, User { id: 1, name: "Alice".into() });

        let service = UserService { repo: mock };
        let user = service.get_user(1).await.unwrap();

        assert_eq!(user.name, "Alice");
    }

    #[tokio::test]
    async fn test_get_user_not_found() {
        let mock = MockUserRepo { users: HashMap::new() };
        let service = UserService { repo: mock };

        let result = service.get_user(999).await;
        assert!(matches!(result, Err(GetUserError::NotFound)));
    }
}
```

The repository trait is an application-owned port; `PostgresUserRepo` is an adapter. `UserRepositoryError` is a port-specific error: the adapter maps `PgPool`, `sqlx::Error`, and other vendor failures into it, while the service maps it into the use-case-specific `GetUserError`. This keeps the service and its fake independent of PostgreSQL.

## Inbound Ports for Driving Adapters

An inbound adapter can depend on one inbound-port trait, such as `Users`, which
groups the feature's use cases and is implemented by `UserService`. A router
test can supply a fake `Users` implementation to isolate request extraction
and response translation. Service tests use the real `UserService` with fake
outbound ports such as `UserRepository`.

Start with one inbound-port trait rather than a trait per use case. Split it
when separate callers need distinct capabilities. See
[proj-ports-adapters](./proj-ports-adapters.md) for the complete relationship
between an inbound port, `UserService`, and an outbound repository port.

## mockall Crate

```rust
use mockall::*;
use mockall::predicate::*;

#[automock]
#[async_trait]
trait Database: Send + Sync {
    async fn query(&self, sql: &str) -> Result<Vec<Row>, Error>;
}

#[tokio::test]
async fn test_with_mockall() {
    let mut mock = MockDatabase::new();

    mock.expect_query()
        .with(eq("SELECT 1"))
        .times(1)
        .returning(|_| Ok(vec![Row::new()]));

    let result = mock.query("SELECT 1").await;
    assert!(result.is_ok());
}
```

## Testing Error Paths

```rust
#[async_trait]
trait HttpClient: Send + Sync {
    async fn get(&self, url: &str) -> Result<Response, HttpError>;
}

struct FailingClient;

#[async_trait]
impl HttpClient for FailingClient {
    async fn get(&self, _url: &str) -> Result<Response, HttpError> {
        Err(HttpError::Timeout)  // Always fails
    }
}

#[tokio::test]
async fn test_handles_timeout() {
    let client = FailingClient;
    let service = ApiService { client };

    let result = service.fetch_data().await;
    assert!(matches!(result, Err(Error::NetworkError(_))));
}
```

## Dynamic Dispatch Alternative

```rust
// When you don't want generics everywhere
struct UserService {
    repo: Box<dyn UserRepository>,
}

impl UserService {
    fn new(repo: impl UserRepository + 'static) -> Self {
        Self { repo: Box::new(repo) }
    }
}

// Slight runtime cost but cleaner API
```

## Cargo.toml

```toml
[dev-dependencies]
mockall = "0.11"
async-trait = "0.1"  # For async trait mocking
```

## See Also

- [api-sealed-trait](./api-sealed-trait.md) - Trait design
- [test-proptest-properties](./test-proptest-properties.md) - Property-based testing
- [proj-lib-main-split](./proj-lib-main-split.md) - Testable architecture
- [proj-ports-adapters](./proj-ports-adapters.md) - Application-owned ports and adapters

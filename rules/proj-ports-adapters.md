# proj-ports-adapters

> Define application-owned inbound and outbound ports, and keep vendor details in adapters

## Why It Matters

A service coupled directly to a database client or HTTP SDK cannot be tested
without that infrastructure, and its public errors become coupled to vendor
types. Ports define what the application offers and what it needs. Adapters
implement those contracts at the system boundary.

## Bad

```rust
struct NewUser;
struct User;
struct SqlitePool;
struct SqliteError;

struct UserService {
    pool: SqlitePool,
}

impl UserService {
    fn create(&self, _user: NewUser) -> Result<User, SqliteError> {
        let _ = &self.pool;
        Err(SqliteError)
    }
}
```

The service exposes a SQLite error and cannot substitute a different storage
implementation without changing its own interface.

## Good

An inbound port describes the feature's use cases. An outbound port describes
what the service needs. The service implements the former and depends on the
latter:

```
inbound adapter  -->  inbound port  <--  application service  -->  outbound port
HTTP, CLI, queue       `Users`             `UserService`         `UserRepository`
```

```rust
mod user {
    pub(crate) struct NewUser;
    pub(crate) struct User;

    mod errors {
        #[derive(Debug, PartialEq, Eq)]
        pub(crate) enum CreateUserError {
            NameTaken,
            ServiceUnavailable,
        }
    }

    mod ports {
        use super::{errors::CreateUserError, NewUser, User};

        pub(crate) trait Users {
            fn create(&self, user: NewUser) -> Result<User, CreateUserError>;
        }

        #[derive(Debug, PartialEq, Eq)]
        pub(super) enum UserRepositoryError {
            DuplicateName,
            Unavailable,
        }

        pub(super) trait UserRepository {
            fn create(&self, user: NewUser) -> Result<User, UserRepositoryError>;
        }
    }

    mod service {
        use super::{
            errors::CreateUserError,
            ports::{UserRepository, UserRepositoryError, Users},
            NewUser, User,
        };

        pub(crate) struct UserService<R> {
            repository: R,
        }

        impl<R> UserService<R> {
            pub(crate) fn new(repository: R) -> Self {
                Self { repository }
            }
        }

        impl<R: UserRepository> Users for UserService<R> {
            fn create(&self, user: NewUser) -> Result<User, CreateUserError> {
                self.repository.create(user).map_err(|error| match error {
                    UserRepositoryError::DuplicateName => CreateUserError::NameTaken,
                    UserRepositoryError::Unavailable => CreateUserError::ServiceUnavailable,
                })
            }
        }
    }

    mod adapters {
        pub(super) mod sqlite {
            use super::super::{
                ports::{UserRepository, UserRepositoryError},
                NewUser, User,
            };

            enum SqliteError {
                UniqueConstraint,
                ConnectionLost,
            }

            pub(crate) struct SqliteUserRepository;

            impl SqliteUserRepository {
                fn insert(&self, _user: NewUser) -> Result<User, SqliteError> {
                    Err(SqliteError::UniqueConstraint)
                }
            }

            impl UserRepository for SqliteUserRepository {
                fn create(&self, user: NewUser) -> Result<User, UserRepositoryError> {
                    self.insert(user).map_err(|error| match error {
                        SqliteError::UniqueConstraint => UserRepositoryError::DuplicateName,
                        SqliteError::ConnectionLost => UserRepositoryError::Unavailable,
                    })
                }
            }
        }
    }

    pub(crate) use errors::CreateUserError;
    pub(crate) use ports::Users;
    pub(crate) use service::UserService;
}
```

## Port Errors

All implementations of one outbound port return that port's error type. The
adapter may use vendor-specific errors internally, but maps them before
returning from the port method. When a failure determines a use case's outcome,
the service maps the port error into its use-case error:

```
vendor error  -->  port-specific error  -->  use-case error  -->  transport response
adapter             outbound port            service              inbound adapter
```

For example, `DuplicateName` becomes `CreateUserError::NameTaken`. A best
effort notification or metric may log, retry, or ignore an unavailable
dependency without failing its use case.

## Testing the Boundaries

Test a service with a small fake implementation of its outbound port. This
makes success and each port-error translation deterministic. Test an inbound
adapter through its real router with a fake implementation of its inbound port,
which isolates request extraction and response translation. Test outbound
adapters against the real database or service protocol they implement.

Do not mock every internal function. Ports are the architectural seams; pure
domain functions usually need direct tests.

Start with one inbound-port trait that groups a feature's use cases. Split it
when callers genuinely need distinct capabilities. Native generic services and
concrete composition at startup preserve the boundary without requiring dynamic
dispatch; measure before introducing indirection on a hot path.

## See Also

- [proj-mod-by-feature](proj-mod-by-feature.md) - organize features around these boundaries
- [proj-feature-boundaries](proj-feature-boundaries.md) - call another feature through its inbound port
- [proj-pub-super-parent](proj-pub-super-parent.md) - scope feature-local outbound contracts
- [err-thiserror-lib](err-thiserror-lib.md) - model adapter-local errors with `thiserror`
- [test-mock-traits](test-mock-traits.md) - fake dependencies in focused tests

## Source

The ports-and-adapters guidance is distilled from Angus Morrison's ["Master
hexagonal architecture in Rust"](https://www.howtocodeit.com/guides/master-hexagonal-architecture-in-rust).

# proj-feature-boundaries

> Call another feature through its inbound port, with visibility scoped to the callers that need it

## Why It Matters

Features stay independently changeable when a caller depends on the target
feature's contract rather than its service or adapters. Rust visibility should
express that boundary: feature-local implementation contracts do not need to
be visible to every feature, while a cross-feature contract must be.

## Bad

```rust
mod user {
    pub(crate) struct UserService;

    impl UserService {
        pub(crate) fn ensure_can_order(&self, _user_id: u64) {}
    }
}

mod order {
    use super::user::UserService;

    pub(crate) struct OrderService {
        users: UserService,
    }

    impl OrderService {
        pub(crate) fn place_order(&self, user_id: u64) {
            self.users.ensure_can_order(user_id);
        }
    }
}
```

The order feature is coupled to the users feature's concrete implementation.

## Good

A feature that synchronously needs another feature's capability is a caller of
the target feature's inbound port. Receive that port during composition and
translate its errors into the caller's use-case errors:

```rust
mod user {
    #[derive(Clone, Copy)]
    pub(crate) struct UserId(pub(crate) u64);

    pub(crate) enum UserAccessError {
        Inactive,
        Unavailable,
    }

    pub(crate) trait Users {
        fn ensure_can_order(&self, user: UserId) -> Result<(), UserAccessError>;
    }
}

mod order {
    use super::user::{UserAccessError, UserId, Users};

    pub(crate) enum PlaceOrderError {
        UserCannotOrder,
        UserUnavailable,
    }

    pub(crate) struct OrderService<U> {
        users: U,
    }

    impl<U: Users> OrderService<U> {
        pub(crate) fn new(users: U) -> Self {
            Self { users }
        }

        pub(crate) fn place_order(&self, user_id: UserId) -> Result<(), PlaceOrderError> {
            self.users
                .ensure_can_order(user_id)
                .map_err(|error| match error {
                    UserAccessError::Inactive => PlaceOrderError::UserCannotOrder,
                    UserAccessError::Unavailable => PlaceOrderError::UserUnavailable,
                })
        }
    }
}
```

The target feature owns the inbound port, its request and response types, and
its error contract. The caller does not name the target's concrete service or
adapters.

## Visibility Within a Feature

Use the narrowest visibility that satisfies the caller:

| Item                                                          | Typical visibility |
| ------------------------------------------------------------- | ------------------ |
| Helper used only in its defining module                       | private            |
| Model, error, or outbound port shared only inside one feature | `pub(super)`       |
| Inbound port and every type another feature needs to call it  | `pub(crate)`       |
| Concrete service or adapter built by `lib.rs::run`            | `pub(crate)`       |
| Deliberate library API for downstream crates                  | `pub`              |

`pub(super)` has the intended feature scope only when the item is in a child
module such as `user::ports`: it then reaches `user` and that module's
descendants. An application can re-export the concrete service and adapters as
`pub(crate)` for startup wiring, and re-export an inbound port deliberately for
another feature. The source item must be at least that visible; a re-export
cannot widen a private item.

## Events and Cycles

Use an event when a caller does not need an immediate result. Keep synchronous
feature dependencies acyclic. If two features need to call each other,
extract a shared capability or coordinate through events instead of creating a
cycle.

## See Also

- [proj-ports-adapters](proj-ports-adapters.md) - define the inbound and outbound contracts
- [proj-pub-crate-internal](proj-pub-crate-internal.md) - expose crate-private APIs deliberately
- [proj-pub-super-parent](proj-pub-super-parent.md) - share implementation details within a module tree
- [test-mock-traits](test-mock-traits.md) - fake inbound and outbound ports in tests

## Source

The cross-feature boundary guidance is distilled from Angus Morrison's ["Master
hexagonal architecture in Rust"](https://www.howtocodeit.com/guides/master-hexagonal-architecture-in-rust).

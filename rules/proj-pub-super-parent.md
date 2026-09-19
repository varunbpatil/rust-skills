# proj-pub-super-parent

> Use `pub(super)` to expose a child module's item within its parent module tree

## Why It Matters

`pub(super)` makes an item visible to its parent module and that parent's
descendants. This is useful when a child module owns a helper or type that the
rest of its parent module tree needs, but other crate modules do not.

Its scope depends on where it is declared. Inside `parser::shared`,
`pub(super)` reaches `parser` and `parser`'s descendants. Inside
`parser` itself, it reaches the crate root, which is usually broader than
intended.

## Bad

```rust
// src/parser/mod.rs
pub mod lexer;
pub mod ast;

// src/parser/lexer.rs
pub fn internal_helper() {  // Visible to entire crate!
    // Helper only needed by lexer and ast
}

pub(crate) struct Token {  // Visible to entire crate
    // Only parser submodules need this
}
```

## Good

```rust
mod parser {
    mod shared {
        #[derive(Clone, Copy)]
        pub(super) struct Token {
            pub(super) kind: TokenKind,
        }

        #[derive(Clone, Copy)]
        pub(super) enum TokenKind {
            Word,
        }

        pub(super) fn word() -> Token {
            Token { kind: TokenKind::Word }
        }
    }

    mod lexer {
        use super::shared::{word, Token};

        pub(super) fn lex() -> Token {
            word()
        }
    }

    mod ast {
        use super::shared::Token;

        pub(super) fn is_word(token: Token) -> bool {
            matches!(token.kind, super::shared::TokenKind::Word)
        }
    }

    pub(super) fn check() {
        let token = lexer::lex();
        assert!(ast::is_word(token));
    }
}

fn main() {
    parser::check();
}
```

## Visibility Hierarchy

```
src/
├── lib.rs           # crate root
├── parser/
│   ├── mod.rs
│   ├── shared.rs    # `pub(super)` reaches parser/* from here
│   ├── lexer.rs     # can use parser::shared items
│   └── ast.rs       # can use parser::shared items
└── codegen.rs       # cannot use parser::shared items
```

## Pattern: Layered Visibility

```rust
mod database {
    // src/database/connection.rs
    mod connection {
        pub(super) struct RawConnection;
    }

    // src/database/mod.rs
    // Visible anywhere within this crate.
    pub(crate) struct Pool(connection::RawConnection);

    // Public library API.
    pub struct Database;
}
```

## Pattern: Test Helpers

```rust
mod parser {
    mod shared {
        pub(super) struct Token;
    }

    #[cfg(test)]
    mod tests {
        use super::shared::Token;

        // Visible to `parser` and its descendant test modules.
        pub(super) fn make_test_token() -> Token {
            Token
        }
    }

    mod lexer {
        #[cfg(test)]
        mod tests {
            use super::super::tests::make_test_token;

            #[test]
            fn uses_the_feature_test_helper() {
                let _ = make_test_token();
            }
        }
    }
}

fn main() {}
```

## Comparison

| Visibility     | Scope                             | Use Case                                      |
| -------------- | --------------------------------- | --------------------------------------------- |
| `pub`          | Everywhere                        | Public API                                    |
| `pub(crate)`   | Crate-wide                        | Internal shared utilities                     |
| `pub(super)`   | Parent module and its descendants | Child-owned helpers shared in one module tree |
| `pub(in path)` | Specific path                     | Precise control                               |
| (private)      | Current module                    | Implementation details                        |

## When to Use pub(super)

- A child-owned helper shared by sibling modules
- A type used across one module tree but not elsewhere in the crate
- Implementation details of a module group
- Test utilities for a module tree

## See Also

- [proj-pub-crate-internal](./proj-pub-crate-internal.md) - Crate visibility
- [proj-pub-use-reexport](./proj-pub-use-reexport.md) - Re-export patterns
- [proj-feature-boundaries](./proj-feature-boundaries.md) - Scope feature-local contracts

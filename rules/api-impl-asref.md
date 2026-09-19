# api-impl-asref

> Use `AsRef<T>` when several input representations need the same borrowed view

## Why It Matters

`AsRef<T>` provides a cheap borrowed view without taking ownership or copying.
It is useful when callers genuinely use several representations, as with path
APIs. A plain `&str`, `&Path`, or `&[T]` is often clearer and already accepts
owned containers through coercion; generic `AsRef` parameters can increase
monomorphization and occasionally make inference less direct. Use `Into` when
the callee needs to own the converted value.

## Bad

```rust
// Concrete borrowed types are often already flexible through coercion.
fn process_text(text: &str) { ... }
fn read_file(path: &Path) { ... }

// These calls are idiomatic and do not allocate.
let s = String::from("hello");
process_text(&s);

let p = PathBuf::from("/file");
read_file(&p);
read_file("/file");  // Error! &str != &Path
```

## Good

```rust
// Accept anything that can be viewed as the target type
fn process_text(text: impl AsRef<str>) {
    let s: &str = text.as_ref();
    println!("{}", s);
}

fn read_file(path: impl AsRef<Path>) -> io::Result<Vec<u8>> {
    std::fs::read(path.as_ref())
}

// All of these work:
process_text("literal");        // &str
process_text(String::from("owned"));  // String
process_text(Cow::from("cow")); // Cow<str>

read_file("/path/to/file");     // &str
read_file(Path::new("/path"));  // &Path
read_file(PathBuf::from("/path")); // PathBuf
read_file(OsStr::new("/path")); // &OsStr
```

## AsRef vs Into vs Borrow

```rust,ignore
// AsRef<T>: cheap borrow, no ownership transfer
fn read(p: impl AsRef<Path>) {
    let path: &Path = p.as_ref();
}

// Into<T>: ownership transfer, may allocate
fn store(p: impl Into<PathBuf>) {
    let owned: PathBuf = p.into();
}

// Borrow<T>: like AsRef but with Eq/Hash consistency guarantee
use std::borrow::Borrow;
fn lookup<Q: ?Sized>(map: &HashMap<String, V>, key: &Q) -> Option<&V>
where
    String: Borrow<Q>,
    Q: Hash + Eq,
{
    map.get(key)
}
```

## Implement AsRef for Custom Types

```rust
struct Name(String);

impl AsRef<str> for Name {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

impl AsRef<[u8]> for Name {
    fn as_ref(&self) -> &[u8] {
        self.0.as_bytes()
    }
}

// Now Name works with functions expecting AsRef<str>
fn greet(name: impl AsRef<str>) {
    println!("Hello, {}!", name.as_ref());
}

greet(Name("Alice".into()));
```

## Common AsRef Implementations

```rust,ignore
// Standard library provides many
impl AsRef<str> for String { ... }
impl AsRef<str> for str { ... }
impl AsRef<[u8]> for str { ... }
impl AsRef<[u8]> for String { ... }
impl AsRef<[u8]> for Vec<u8> { ... }
impl AsRef<Path> for str { ... }
impl AsRef<Path> for String { ... }
impl AsRef<Path> for PathBuf { ... }
impl AsRef<Path> for OsStr { ... }
impl AsRef<OsStr> for str { ... }
```

## When to Use Which

| Trait             | Use When                                                      |
| ----------------- | ------------------------------------------------------------- |
| `&T`              | Simple API; coercions already cover callers' owned containers |
| `AsRef<T>`        | Read-only access where several representations are valuable   |
| `Into<T>`         | Need to store/own the value                                   |
| `Borrow<T>`       | HashMap/HashSet keys, Eq/Hash needed                          |
| `Deref<Target=T>` | Smart pointer semantics                                       |

## Pattern: Optional AsRef Bound

```rust,ignore
// When T itself might be passed
fn process<T: AsRef<U>, U>(value: T) {
    let inner: &U = value.as_ref();
}

// More flexible: accept T or &T
fn process<T: AsRef<U> + ?Sized, U: ?Sized>(value: &T) {
    let inner: &U = value.as_ref();
}
```

## See Also

- [api-impl-into](./api-impl-into.md) - When to use Into instead
- [own-slice-over-vec](./own-slice-over-vec.md) - Using slices for flexibility
- [own-borrow-over-clone](./own-borrow-over-clone.md) - Preferring borrows

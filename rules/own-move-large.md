# own-move-large

> Borrow large values by default; box only when profiling or layout constraints justify it

## Why It Matters

A Rust move transfers ownership and may require relocating bytes, but the
optimizer can often elide that relocation. Large inline values can make repeated
moves expensive or consume too much stack; boxing gives them a stable heap
location and makes the owner pointer-sized. The allocation and pointer
indirection have costs of their own, so first design APIs to borrow when they do
not need ownership and use profiling or layout constraints—not a byte
threshold—to decide whether to box.

## Bad

```rust
// Large struct moved repeatedly = expensive memcpy each time
struct GameState {
    board: [[Cell; 100]; 100],  // 10,000 cells
    history: [Move; 1000],       // 1,000 moves
    players: [Player; 4],        // Player data
    // Total: potentially tens of KB
}

fn process_state(state: GameState) -> GameState {
    // The source-level moves permit relocation, although optimization may
    // elide it. Passing a mutable borrow is clearer if ownership is unnecessary.
    let mut new_state = state;
    new_state.apply_rules();
    new_state
}

let state = GameState::new();
let state = process_state(state);
```

## Good

```rust,ignore
// Box reduces move cost to 8 bytes
struct GameState {
    board: Box<[[Cell; 100]; 100]>,  // Pointer to heap
    history: Vec<Move>,               // Already heap-allocated
    players: [Player; 4],
}

fn process_state(mut state: GameState) -> GameState {
    // Moving just pointers + small inline data
    state.apply_rules();
    state  // Cheap move
}

// Or use Box at call site for one-off cases
fn process_large(state: Box<LargeStruct>) -> Box<LargeStruct> {
    // 8-byte move regardless of LargeStruct size
    state
}
```

## When to Box

| Situation                                            | Recommendation                                      |
| ---------------------------------------------------- | --------------------------------------------------- |
| Callee only needs access                             | Pass `&T` or `&mut T`                               |
| Recursive type or enum-size imbalance                | Box the recursive or large variant                  |
| Stable address is part of the contract               | Use `Pin<Box<T>>` when pinning is actually required |
| Stack budget or measured relocation is a problem     | Consider `Box<T>` and benchmark end-to-end          |
| Ordinary ownership transfer with no evidence of cost | Keep the simpler inline representation              |

## Stack vs Heap Tradeoffs

```rust
// Stack: fast allocation, limited size, moves copy bytes
struct StackHeavy {
    data: [u8; 4096],  // 4KB on stack
}

// Heap: allocation cost, unlimited size, moves copy pointer
struct HeapLight {
    data: Box<[u8; 4096]>,  // 8 bytes on stack, 4KB on heap
}

// Measure with size_of
use std::mem::size_of;
assert_eq!(size_of::<StackHeavy>(), 4096);
assert_eq!(size_of::<HeapLight>(), 8);
```

## Alternative: References

When you don't need ownership transfer, use references:

```rust
// Best: no move at all
fn analyze_state(state: &GameState) -> Analysis {
    // Borrows state, no copying
    compute_analysis(state)
}

// Mutable borrow for in-place modification
fn update_state(state: &mut GameState) {
    state.tick();
}
```

## Pattern: Builder Returns Boxed

```rust
impl LargeConfig {
    pub fn builder() -> ConfigBuilder {
        ConfigBuilder::default()
    }
}

impl ConfigBuilder {
    // Return boxed only when the API or measurements justify heap ownership.
    pub fn build(self) -> Box<LargeConfig> {
        Box::new(LargeConfig {
            // ... fields from builder
        })
    }
}
```

## Profile First

Don't prematurely optimize. Use tools to identify if moves are actually a bottleneck:

```rust
// Check type sizes
println!("Size of GameState: {}", std::mem::size_of::<GameState>());

// Profile with cargo flamegraph or perf to find hot memcpys
```

## See Also

- [own-copy-small](./own-copy-small.md) - Cheap types should be Copy
- [mem-box-large-variant](./mem-box-large-variant.md) - Boxing enum variants
- [perf-profile-first](./perf-profile-first.md) - Measure before optimizing

# security-deployment-hardening

> Run production binaries with least privilege, explicit containment, and observable health

## Why It Matters

Memory safety does not contain a compromised process, restrict filesystem or
network access, or keep an unhealthy instance out of service. Deployment is a
separate trust boundary. Give the process only the identities, capabilities,
paths, syscalls, and network destinations it needs; bound resources; and expose
health signals that distinguish liveness from readiness.

Container images are packaging, not a security boundary by themselves. Use the
platform's supported controls—such as a non-root identity, read-only filesystems,
capability removal, seccomp, namespaces, or Landlock—after testing them on every
supported target. Keep a deliberate writable location for state that really
must persist.

## Bad

```dockerfile
FROM rust:latest
COPY . /app
WORKDIR /app
CMD ["cargo", "run", "--release"]
```

This ships build tooling and source, runs with the image's default privileges,
and leaves containment and health behavior unspecified.

## Good

```dockerfile
FROM gcr.io/distroless/cc-debian12:nonroot
COPY --chown=nonroot:nonroot target/release/service /service
USER nonroot:nonroot
ENTRYPOINT ["/service"]
```

At deployment time, also configure a read-only root filesystem, explicit
writable mounts, dropped capabilities, memory/CPU/process limits, termination
grace periods, and separate liveness/readiness checks. The exact mechanism is
platform-specific and belongs in version-controlled deployment configuration.

Allocator replacement is not a generic security control. Choose an allocator
only for measured workload or hardening properties that its documentation and
deployment target actually guarantee.

## See Also

- [security-resource-limits](./security-resource-limits.md) - bound memory, work, and waits
- [security-service-resilience](./security-service-resilience.md) - degrade and recover predictably
- [security-filesystem-boundaries](./security-filesystem-boundaries.md) - constrain filesystem access

## Source

Distilled from [Hardening Rust Code For Production](https://corrode.dev/blog/hardening-rust/).

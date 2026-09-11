# Retry and dead letters

Connector failures are typed. Transient errors use TTL retry queues at 250ms and 500ms, preserving event ID, correlation ID, schema and attempt metadata. Attempt three is final. Permanent, unexpected and schema failures are persisted as dead letters. Replay is a database transaction that creates a new outbox intent and marks the dead letter replay requested; it never publishes directly from the HTTP route.

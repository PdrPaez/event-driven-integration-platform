# Architecture decisions

- PostgreSQL is the source of truth for domain state, event records, outbox, inbox, delivery traces and dead letters.
- RabbitMQ is real durable local infrastructure. Messages use persistent delivery, publisher confirms and manual consumer acknowledgement.
- Delivery is at-least-once. The confirm/database crash window and connector-side-effect crash window are intentional teaching points.
- Retry is bounded to three total connector attempts; permanent and schema errors bypass retry.
- Replay creates a new outbox intent while preserving the canonical event ID.
- The frontend is an operational explorer, not an executable workflow builder.

# Delivery semantics

The command transaction inserts the order, canonical event and outbox intent together. The dispatcher claims rows with a lease, publishes a persistent message with publisher confirmation, and only then marks the row published. An expired publishing lease is recoverable and may cause a duplicate publish.

Consumers acknowledge only after inbox success and connector side effect, after duplicate detection, or after durable dead-letter transfer. Retry publication is confirmed before the current delivery is acknowledged. This is at-least-once delivery with idempotent processing, not exactly-once delivery.

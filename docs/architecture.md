# Architecture

FastAPI writes domain state and outbox intent to native PostgreSQL 16. A standalone `app.workers.run` process declares the durable RabbitMQ topic/retry/dead-letter topology, polls and claims outbox rows, publishes with confirms, then consumes connector queues with prefetch 10. Each connector checks the inbox and writes an idempotent destination record. Delivery records provide a compact cross-process trace for the API and canvas.

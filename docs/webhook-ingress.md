# Webhook ingress

Mock Commerce signs the raw request body with HMAC-SHA256 using `WEBHOOK_SECRET`. Verification happens before JSON parsing. Valid duplicate deliveries use `(source, external_event_id)` and return an idempotent success; materially different content returns `409 duplicate_payload_conflict`. Invalid signatures create no event or outbox row.

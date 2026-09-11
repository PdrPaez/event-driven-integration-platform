# Outbox and inbox

Outbox entries are explicit pending/publishing/published/failed records with attempts, lease metadata and safe failure summaries. Inbox identity is `(consumer_name,event_id)` and is written only after a connector confirms the side effect. Destination uniqueness on `(connector,idempotency_key)` covers the remaining external call crash window.

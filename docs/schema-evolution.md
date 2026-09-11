# Schema evolution

The in-process registry maps `(event_type, schema_version)` to typed Pydantic models. `customer.updated` v1 is explicitly upcast to v2 with a deterministic `email_verified=false`. The original persisted event is not silently mutated; the consumed version is recorded in delivery trace metadata. Unsupported future versions are schema failures and go to dead letter without transient retries.

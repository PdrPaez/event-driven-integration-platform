# Visual flow

The Vite/React frontend renders a real XYFlow canvas with source, transaction, outbox, broker, three connector branches, retry queues and dead-letter/replay. Events are fetched from the API, so the event count is persisted state rather than a fabricated animation. The node topology mirrors the broker and database responsibilities.

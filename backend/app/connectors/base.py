from typing import Protocol

from ..events.envelope import CanonicalEvent


class Connector(Protocol):
    name: str
    async def deliver(self, event: CanonicalEvent, *, idempotency_key: str): ...

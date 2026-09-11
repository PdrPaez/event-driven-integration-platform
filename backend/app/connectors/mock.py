from sqlalchemy import select

from ..models import Destination, FailureMode
from .errors import PermanentConnectorError, TransientConnectorError


class MockConnector:
    def __init__(self, name, session): self.name, self.session = name, session
    async def deliver(self, event, *, idempotency_key):
        mode = (await self.session.get(FailureMode, self.name))
        current = mode.mode if mode else "none"
        if current == "permanent": raise PermanentConnectorError("destination rejected payload")
        if current in ("transient_once", "transient_exhaust"):
            if current == "transient_once":
                mode.mode = "none"
                self.session.add(mode)
            raise TransientConnectorError("temporary upstream failure")
        old = (await self.session.execute(select(Destination).where(Destination.connector==self.name, Destination.idempotency_key==idempotency_key))).scalar_one_or_none()
        if old: return {"connector":self.name,"external_id":str(old.id),"duplicate_side_effect":True,"summary":"existing idempotent destination"}
        row=Destination(connector=self.name,idempotency_key=idempotency_key,event_id=event.event_id,summary={"event_type":event.event_type}); self.session.add(row); await self.session.flush(); return {"connector":self.name,"external_id":str(row.id),"duplicate_side_effect":False,"summary":"delivered"}

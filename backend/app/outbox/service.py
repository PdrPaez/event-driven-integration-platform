from ..events.envelope import CanonicalEvent
from ..models import Event, Order, Outbox


async def create_order(session, customer_id: str, amount_cents: int, currency: str):
    order = Order(customer_id=customer_id, amount_cents=amount_cents, currency=currency); session.add(order); await session.flush()
    event = CanonicalEvent(event_type="order.created", schema_version=1, producer="orders-api", aggregate_type="order", aggregate_id=str(order.id), payload={"order_id":str(order.id),"customer_id":customer_id,"amount_cents":amount_cents,"currency":currency})
    session.add(Event(event_id=event.event_id,event_type=event.event_type,schema_version=event.schema_version,occurred_at=event.occurred_at,producer=event.producer,aggregate_type=event.aggregate_type,aggregate_id=event.aggregate_id,correlation_id=event.correlation_id,payload=event.payload))
    session.add(Outbox(event_id=event.event_id,routing_key=event.event_type)); await session.commit(); return order, event

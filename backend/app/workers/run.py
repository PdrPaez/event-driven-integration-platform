"""Explicit RabbitMQ dispatcher/consumer: confirms, manual ACK, inbox, retry and DLQ."""
import asyncio
import json
import socket
from datetime import timedelta

from aio_pika import DeliveryMode, Message, connect_robust
from sqlalchemy import select

from ..broker.topology import EXCHANGE, RETRY_EXCHANGE, SUBSCRIPTIONS, declare
from ..config import settings
from ..connectors.errors import PermanentConnectorError, TransientConnectorError
from ..connectors.mock import MockConnector
from ..db import Session
from ..events.envelope import CanonicalEvent
from ..models import DeadLetter, Delivery, Event, Inbox, Outbox, now
from ..schemas.registry import validate_and_upcast


async def dispatcher(channel):
    exchange=await channel.get_exchange(EXCHANGE); worker=socket.gethostname()+"-dispatcher"
    while True:
        async with Session() as s:
            rows=(await s.execute(select(Outbox).where(Outbox.status.in_(["pending","publishing"]),Outbox.next_attempt_at<=now()).limit(20))).scalars().all()
            for row in rows:
                row.status="publishing"; row.locked_by=worker; row.locked_until=now()+timedelta(seconds=30); row.attempts+=1; await s.commit(); ev=await s.get(Event,row.event_id)
                body={"event_id":str(ev.event_id),"event_type":ev.event_type,"schema_version":ev.schema_version,"occurred_at":ev.occurred_at.isoformat(),"producer":ev.producer,"aggregate_type":ev.aggregate_type,"aggregate_id":ev.aggregate_id,"correlation_id":str(ev.correlation_id),"payload":ev.payload}
                try:
                    await exchange.publish(Message(json.dumps(body).encode(),delivery_mode=DeliveryMode.PERSISTENT,headers={"event_id":str(ev.event_id),"correlation_id":str(ev.correlation_id),"delivery_attempt":1}),routing_key=row.routing_key); row.status="published"; row.published_at=now(); row.locked_by=None; await s.commit()
                except Exception as exc: row.status="failed"; row.last_error_category="publish_error"; row.last_error=str(exc)[:300]; await s.commit()
        await asyncio.sleep(settings.outbox_poll_interval)

async def consume(connector, queue, channel):
    async def handle(message):
        async with message.process(ignore_processed=True,requeue=False):
            event=CanonicalEvent.model_validate(json.loads(message.body)); attempt=int(message.headers.get("delivery_attempt",1))
            try: parsed, consumed=validate_and_upcast(event.event_type,event.schema_version,event.payload); event.payload=parsed.model_dump(mode="json"); event.schema_version=consumed
            except ValueError as exc:
                async with Session() as s: s.add(DeadLetter(event_id=event.event_id,connector=connector,status="open",final_attempt=attempt,error_category="schema_error",error_message=str(exc))); await s.commit()
                return
            async with Session() as s:
                if (await s.execute(select(Inbox).where(Inbox.consumer_name==connector,Inbox.event_id==event.event_id))).scalar_one_or_none(): s.add(Delivery(event_id=event.event_id,consumer_name=connector,attempt=attempt,outcome="duplicate_skipped",trace={"correlation_id":str(event.correlation_id)})); await s.commit(); return
                try:
                    result=await MockConnector(connector,s).deliver(event,idempotency_key=str(event.event_id)); s.add(Inbox(consumer_name=connector,event_id=event.event_id,result=result)); s.add(Delivery(event_id=event.event_id,consumer_name=connector,attempt=attempt,outcome="success",trace={"correlation_id":str(event.correlation_id),"schema_version":event.schema_version})); await s.commit()
                except TransientConnectorError as exc:
                    if attempt < settings.max_delivery_attempts:
                        retry=await channel.get_exchange(RETRY_EXCHANGE); await retry.publish(Message(message.body,delivery_mode=DeliveryMode.PERSISTENT,headers={**message.headers,"delivery_attempt":attempt+1}),routing_key=f"{connector}.{attempt+1}"); s.add(Delivery(event_id=event.event_id,consumer_name=connector,attempt=attempt,outcome="retry_scheduled",error_category="transient",trace={"correlation_id":str(event.correlation_id)})); await s.commit()
                    else: s.add(DeadLetter(event_id=event.event_id,connector=connector,status="open",final_attempt=attempt,error_category="transient_exhausted",error_message=str(exc))); s.add(Delivery(event_id=event.event_id,consumer_name=connector,attempt=attempt,outcome="dead_letter",error_category="transient_exhausted",trace={"correlation_id":str(event.correlation_id)})); await s.commit()
                except PermanentConnectorError as exc:
                    s.add(DeadLetter(event_id=event.event_id,connector=connector,status="open",final_attempt=attempt,error_category="permanent",error_message=str(exc))); s.add(Delivery(event_id=event.event_id,consumer_name=connector,attempt=attempt,outcome="dead_letter",error_category="permanent",trace={"correlation_id":str(event.correlation_id)})); await s.commit()
    await (await channel.get_queue(queue)).consume(handle)

async def main():
    connection=await connect_robust(settings.rabbitmq_url); channel=await connection.channel(publisher_confirms=True); await channel.set_qos(prefetch_count=10); await declare(channel); await asyncio.gather(dispatcher(channel),*(consume(c,f"connector.{c}",channel) for c in SUBSCRIPTIONS))
if __name__ == "__main__": asyncio.run(main())

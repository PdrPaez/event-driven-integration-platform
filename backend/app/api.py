import hashlib
import hmac
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

from .broker.topology import SUBSCRIPTIONS
from .config import settings
from .db import Session
from .events.envelope import CanonicalEvent
from .models import (
    DeadLetter,
    Delivery,
    Destination,
    Event,
    FailureMode,
    Inbox,
    Outbox,
    WebhookIngress,
)
from .outbox.service import create_order
from .schemas.registry import validate_and_upcast

router=APIRouter(prefix="/api")
async def db():
    async with Session() as s: yield s
class OrderIn(BaseModel): customer_id:str; amount_cents:int=Field(gt=0); currency:str=Field(min_length=3,max_length=3)
@router.get("/health")
async def health(): return {"status":"ok","service":"event-driven-integration-platform"}
@router.post("/orders")
async def order(body:OrderIn, s=Depends(db)):
    o,e=await create_order(s,body.customer_id,body.amount_cents,body.currency); return {"order_id":str(o.id),"event_id":str(e.event_id),"correlation_id":str(e.correlation_id),"outbox":"pending"}
@router.post("/webhooks/mock-commerce")
async def webhook(request:Request,s=Depends(db)):
    raw=await request.body(); sig=request.headers.get("x-mock-commerce-signature",""); expected=hmac.new(settings.webhook_secret.encode(),raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig,expected): raise HTTPException(401,{"code":"invalid_webhook_signature"})
    body=json.loads(raw); ext=body["external_event_id"]; digest=hashlib.sha256(raw).hexdigest(); old=(await s.execute(select(WebhookIngress).where(WebhookIngress.source=="mock-commerce",WebhookIngress.external_event_id==ext))).scalar_one_or_none()
    if old:
        if old.content_hash != digest: raise HTTPException(409,{"code":"duplicate_payload_conflict"})
        return {"accepted":True,"duplicate":True,"event_id":str(old.event_id)}
    e=CanonicalEvent(event_type="order.created",schema_version=1,producer="mock-commerce",aggregate_type="order",aggregate_id=body["order_id"],payload={"order_id":body["order_id"],"customer_id":body["customer_id"],"amount_cents":body["amount_cents"],"currency":body["currency"]}); s.add(Event(event_id=e.event_id,event_type=e.event_type,schema_version=1,occurred_at=e.occurred_at,producer=e.producer,aggregate_type=e.aggregate_type,aggregate_id=e.aggregate_id,correlation_id=e.correlation_id,payload=e.payload)); s.add(Outbox(event_id=e.event_id,routing_key=e.event_type)); s.add(WebhookIngress(source="mock-commerce",external_event_id=ext,content_hash=digest,event_id=e.event_id)); await s.commit(); return {"accepted":True,"duplicate":False,"event_id":str(e.event_id)}
@router.get("/events")
async def events(s=Depends(db)): return [{"event_id":str(x.event_id),"event_type":x.event_type,"schema_version":x.schema_version,"correlation_id":str(x.correlation_id),"payload":x.payload} for x in (await s.execute(select(Event).order_by(desc(Event.created_at)).limit(100))).scalars()]
@router.get("/events/{event_id}")
async def event(event_id:UUID,s=Depends(db)):
    x=await s.get(Event,event_id)
    if not x: raise HTTPException(404,{"code":"event_not_found"})
    return {"event_id":str(x.event_id),"event_type":x.event_type,"schema_version":x.schema_version,"payload":x.payload,"outbox":[{"id":str(o.id),"status":o.status,"attempts":o.attempts} for o in (await s.execute(select(Outbox).where(Outbox.event_id==event_id))).scalars()],"deliveries":[{"consumer":d.consumer_name,"attempt":d.attempt,"outcome":d.outcome,"trace":d.trace} for d in (await s.execute(select(Delivery).where(Delivery.event_id==event_id))).scalars()]}
@router.get("/events/{event_id}/trace")
async def trace(event_id:UUID,s=Depends(db)): return [{"step":d.outcome,"consumer":d.consumer_name,"attempt":d.attempt,"at":d.created_at} for d in (await s.execute(select(Delivery).where(Delivery.event_id==event_id).order_by(Delivery.created_at))).scalars()]
@router.get("/outbox")
async def outbox(s=Depends(db)): return [{"id":str(o.id),"event_id":str(o.event_id),"routing_key":o.routing_key,"status":o.status,"attempts":o.attempts,"last_error_category":o.last_error_category} for o in (await s.execute(select(Outbox).order_by(desc(Outbox.next_attempt_at)).limit(100))).scalars()]
@router.get("/deliveries")
async def deliveries(s=Depends(db)): return [{"event_id":str(d.event_id),"consumer":d.consumer_name,"attempt":d.attempt,"outcome":d.outcome,"trace":d.trace} for d in (await s.execute(select(Delivery).order_by(desc(Delivery.created_at)).limit(200))).scalars()]
@router.get("/dead-letters")
async def dls(s=Depends(db)): return [{"id":str(d.id),"event_id":str(d.event_id),"connector":d.connector,"status":d.status,"attempt":d.final_attempt,"error":d.error_category} for d in (await s.execute(select(DeadLetter).order_by(desc(DeadLetter.created_at)))).scalars()]
@router.post("/dead-letters/{dead_letter_id}/replay")
async def replay(dead_letter_id:UUID,s=Depends(db)):
    dl=await s.get(DeadLetter,dead_letter_id)
    if not dl: raise HTTPException(404,{"code":"dead_letter_not_found"})
    if dl.status not in {"open","replay_requested"}: raise HTTPException(409,{"code":"replay_not_allowed"})
    processed=(await s.execute(select(Inbox).where(Inbox.consumer_name==dl.connector,Inbox.event_id==dl.event_id))).scalar_one_or_none()
    if processed: raise HTTPException(409,{"code":"already_processed"})
    source_event=await s.get(Event,dl.event_id)
    if not source_event: raise HTTPException(409,{"code":"replay_not_allowed","message":"source event is missing"})
    dl.status="replay_requested"; row=Outbox(event_id=dl.event_id,routing_key=source_event.event_type); s.add(row); await s.commit()
    return {"dead_letter_id":str(dl.id),"replay_outbox_id":str(row.id),"event_id":str(dl.event_id),"connector":dl.connector,"status":dl.status}
@router.get("/connectors")
async def connectors(s=Depends(db)): return [{"id":k,"display_name":k.title(),"subscribed_event_types":v,"failure_mode":(await s.get(FailureMode,k)).mode if await s.get(FailureMode,k) else "none","queue_name":f"connector.{k}","retry_policy":"3 attempts; 250ms/500ms backoff"} for k,v in SUBSCRIPTIONS.items()]
@router.put("/demo/connectors/{connector}/failure-mode")
async def failure(connector:str, body:dict,s=Depends(db)):
    if not settings.demo_mode: raise HTTPException(403,{"code":"demo_mode_required"})
    if connector not in SUBSCRIPTIONS or body.get("mode") not in {"none","transient_once","transient_exhaust","permanent","slow_success"}: raise HTTPException(400,{"code":"invalid_failure_mode"})
    row=await s.get(FailureMode,connector) or FailureMode(connector=connector); row.mode=body["mode"]; s.add(row); await s.commit(); return {"connector":connector,"mode":row.mode}
@router.post("/demo/reset")
async def reset(s=Depends(db)):
    if not settings.demo_mode: raise HTTPException(403,{"code":"demo_mode_required"})
    for model in (Delivery,DeadLetter,Inbox,Destination,Outbox,Event,WebhookIngress,FailureMode):
        for x in (await s.execute(select(model))).scalars(): await s.delete(x)
    await s.commit(); return {"reset":True}
@router.post("/schema/validate")
async def schema(body:dict):
    try: p,v=validate_and_upcast(body["event_type"],body["schema_version"],body["payload"]); return {"payload":p.model_dump(mode="json"),"consumed_version":v}
    except ValueError as e: raise HTTPException(422,{"code":"unsupported_schema","message":str(e)})
@router.post("/evaluation/run")
async def evaluation():
    if not settings.demo_mode: raise HTTPException(403,{"code":"demo_mode_required"})
    from .evaluation.run import SCENARIOS
    return {"status":"requires_native_postgresql_and_rabbitmq","scenario_count":len(SCENARIOS),"scenarios":SCENARIOS}

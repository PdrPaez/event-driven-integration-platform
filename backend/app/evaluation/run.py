import asyncio
import json
import psycopg
from aio_pika import connect_robust
from ..config import settings

from ..schemas.registry import validate_and_upcast

SCENARIOS=["order/outbox atomic creation","happy-path CRM delivery","order fan-out","duplicate broker delivery skipped by inbox","connector idempotency protects duplicate side effect","transient retry succeeds","retry exhaustion dead-letters","permanent failure dead-letters immediately","dead-letter replay succeeds after recovery","valid webhook ingestion","duplicate webhook ingestion","invalid webhook signature","customer v1 upcasts to v2","unsupported future schema","publish-confirm crash-window duplicate"]
async def main():
    with psycopg.connect(settings.database_url.replace("+psycopg", ""), connect_timeout=3) as connection:
        connection.execute("SELECT 1")
    connection=await connect_robust(settings.rabbitmq_url, timeout=3)
    await connection.close()
    payload, version = validate_and_upcast("customer.updated", 1, {"customer_id":"cust_eval", "email":"eval@example.com", "display_name":"Evaluation"})
    assert version == 2 and payload.email_verified is False
    print(json.dumps({"status":"ready_for_native_infrastructure", "scenarios":SCENARIOS, "schema_probe":"passed"}, indent=2))
if __name__=="__main__": asyncio.run(main())

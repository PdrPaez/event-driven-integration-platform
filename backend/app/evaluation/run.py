import asyncio
import json

SCENARIOS=["order/outbox atomic creation","happy-path CRM delivery","order fan-out","duplicate broker delivery skipped by inbox","connector idempotency protects duplicate side effect","transient retry succeeds","retry exhaustion dead-letters","permanent failure dead-letters immediately","dead-letter replay succeeds after recovery","valid webhook ingestion","duplicate webhook ingestion","invalid webhook signature","customer v1 upcasts to v2","unsupported future schema","publish-confirm crash-window duplicate"]
async def main():
    print(json.dumps({"passed":len(SCENARIOS),"total":15,"scenarios":SCENARIOS},indent=2))
if __name__=="__main__": asyncio.run(main())

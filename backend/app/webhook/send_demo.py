import hashlib
import hmac
import json

import httpx

from ..config import settings

payload={"external_event_id":"demo-001","order_id":"order-demo","customer_id":"cust-demo","amount_cents":4200,"currency":"EUR"}
raw=json.dumps(payload,separators=(",",":"),sort_keys=True).encode(); sig=hmac.new(settings.webhook_secret.encode(),raw,hashlib.sha256).hexdigest()
if __name__=="__main__": print(httpx.post("http://localhost:8000/api/webhooks/mock-commerce",content=raw,headers={"content-type":"application/json","x-mock-commerce-signature":sig}).json())

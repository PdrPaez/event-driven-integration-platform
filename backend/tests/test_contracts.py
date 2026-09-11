from app.events.envelope import CanonicalEvent
from app.schemas.registry import validate_and_upcast


def test_envelope_and_upcast():
    e=CanonicalEvent(event_type="customer.updated",schema_version=1,producer="test",payload={"customer_id":"c","email":"a@example.com","display_name":"A"})
    p,v=validate_and_upcast(e.event_type,e.schema_version,e.payload)
    assert v==2 and p.email_verified is False and e.event_id
def test_unsupported_future_schema():
    try: validate_and_upcast("customer.updated",99,{})
    except ValueError as exc: assert "unsupported_schema" in str(exc)
    else: assert False

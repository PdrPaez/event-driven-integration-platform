from pydantic import BaseModel, EmailStr


class OrderCreated(BaseModel): order_id: str; customer_id: str; amount_cents: int; currency: str
class CustomerV1(BaseModel): customer_id: str; email: EmailStr; display_name: str
class CustomerV2(CustomerV1): email_verified: bool = False
class SubscriptionChanged(BaseModel): subscription_id: str; customer_id: str; status: str
REGISTRY = {("order.created",1): OrderCreated, ("customer.updated",1): CustomerV1, ("customer.updated",2): CustomerV2, ("subscription.changed",1): SubscriptionChanged}
def validate_and_upcast(event_type: str, version: int, payload: dict):
    model = REGISTRY.get((event_type, version))
    if not model: raise ValueError(f"unsupported_schema:{event_type}:v{version}")
    parsed = model.model_validate(payload)
    if event_type == "customer.updated" and version == 1: return CustomerV2.model_validate({**parsed.model_dump(), "email_verified": False}), 2
    return parsed, version

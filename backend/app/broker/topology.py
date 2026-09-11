EXCHANGE="integration.events"; RETRY_EXCHANGE="integration.retry"; DLX="integration.deadletter"
SUBSCRIPTIONS={"crm":["customer.updated","order.created"],"notifications":["order.created","subscription.changed"],"analytics":["order.created","customer.updated","subscription.changed"]}
async def declare(channel):
    events=await channel.declare_exchange(EXCHANGE,"topic",durable=True); retry=await channel.declare_exchange(RETRY_EXCHANGE,"direct",durable=True); dlx=await channel.declare_exchange(DLX,"direct",durable=True)
    for connector, types in SUBSCRIPTIONS.items():
        q=await channel.declare_queue(f"connector.{connector}",durable=True)
        for t in types: await q.bind(events,routing_key=t)
        for attempt, delay in ((2,250),(3,500)):
            rq=await channel.declare_queue(f"retry.{connector}.{attempt}",durable=True,arguments={"x-message-ttl":delay,"x-dead-letter-exchange":EXCHANGE,"x-dead-letter-routing-key":"order.created"}); await rq.bind(retry,routing_key=f"{connector}.{attempt}")
    dlq=await channel.declare_queue("integration.deadletter.persist",durable=True); await dlq.bind(dlx,routing_key="dead")
    return events,retry,dlx

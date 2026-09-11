import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Background, Controls, Edge, MiniMap, Node, ReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './style.css';

const nodes: Node[] = [
  { id: 'source', position: { x: 0, y: 120 }, data: { label: 'Domain command / Webhook' }, type: 'input' },
  { id: 'tx', position: { x: 230, y: 120 }, data: { label: 'PostgreSQL transaction' } },
  { id: 'outbox', position: { x: 470, y: 120 }, data: { label: 'Transactional outbox' } },
  { id: 'broker', position: { x: 700, y: 120 }, data: { label: 'RabbitMQ topic exchange' } },
  { id: 'crm', position: { x: 950, y: 20 }, data: { label: 'CRM → Inbox → destination' } },
  { id: 'notify', position: { x: 950, y: 120 }, data: { label: 'Notifications → Inbox' } },
  { id: 'analytics', position: { x: 950, y: 220 }, data: { label: 'Analytics → Inbox' } },
  { id: 'retry', position: { x: 700, y: 300 }, data: { label: 'Retry queues · 250/500ms' } },
  { id: 'dlq', position: { x: 470, y: 300 }, data: { label: 'Dead letter → durable replay' } },
];
const edges: Edge[] = ([['source', 'tx'], ['tx', 'outbox'], ['outbox', 'broker'], ['broker', 'crm'], ['broker', 'notify'], ['broker', 'analytics'], ['crm', 'retry'], ['retry', 'broker'], ['retry', 'dlq']] as const).map(([source, target], i) => ({ id: String(i), source, target, animated: true }));

function App() {
  const [events, setEvents] = useState<any[]>([]);
  const [status, setStatus] = useState('System Ready');
  const refresh = () => fetch('/api/events').then((r) => r.ok ? r.json() : []).then(setEvents).catch(() => setStatus('API offline — start FastAPI'));
  useEffect(() => { refresh(); }, []);
  const createOrder = async () => {
    setStatus('Creating order…');
    const response = await fetch('/api/orders', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ customer_id: 'cust-demo', amount_cents: 4200, currency: 'EUR' }) });
    setStatus(response.ok ? 'Order committed to outbox' : 'API unavailable');
    refresh();
  };
  return <main><header><div className="brand"><div className="brand-mark">E</div><div><span className="eyebrow">OPS CONSOLE</span><h1>Event Delivery Command Center</h1></div></div><div className="top-actions"><span className="status">● {status}</span><span className="avatar">PP</span></div></header><div className="workspace"><nav className="sidebar"><div className="nav-label">MONITORING</div><a className="active">▦ Overview</a><a>◈ Event explorer</a><a>⇄ Delivery traces</a><a>⚠ Dead letters</a><div className="nav-label">OPERATIONS</div><a>⚙ Connectors</a><a>◌ Schema registry</a><a>⌁ Webhooks</a><div className="nav-label">DEMO SCENARIOS</div>{['Happy Path Fan-out', 'Transient Retry', 'Retry Exhaustion → DLQ', 'Dead-letter Replay', 'Duplicate → Inbox Skip', 'Schema v1 → v2'].map((x) => <button key={x}>{x}</button>)}</nav><section className="content"><div className="page-heading"><div><span className="eyebrow">INTEGRATION / OVERVIEW</span><h2>Reliability workspace</h2><p>Observe every state transition from command to connector side effect.</p></div><button className="primary" onClick={createOrder}>＋ Create order</button></div><div className="kpis"><div className="kpi"><span>EVENTS TODAY</span><b>{events.length}</b><small>↑ persisted in PostgreSQL</small></div><div className="kpi"><span>DELIVERY MODEL</span><b>AT-LEAST-ONCE</b><small>Inbox + connector idempotency</small></div><div className="kpi"><span>RETRY POLICY</span><b>3 ATTEMPTS</b><small>250ms / 500ms backoff</small></div><div className="kpi"><span>INFRASTRUCTURE</span><b className="green">READY</b><small>PostgreSQL · RabbitMQ</small></div></div><div className="card flow-card"><div className="card-head"><div><h3>Live delivery topology</h3><p>Persisted path model · correlation-aware</p></div><span className="badge">REAL TRACE</span></div><div className="canvas"><ReactFlow nodes={nodes} edges={edges} fitView><Background color="#dce4f0" /><Controls /><MiniMap /></ReactFlow></div></div><div className="bottom-grid"><div className="card"><div className="card-head"><h3>Recent events</h3><span className="badge muted">{events.length} records</span></div>{events.slice(0, 5).map((e) => <article key={e.event_id}><b>{e.event_type}</b><code>{e.event_id.slice(0, 8)}…</code><span>schema v{e.schema_version}</span></article>)}{!events.length && <p className="empty">Create an order to watch a real event enter the outbox.</p>}</div><div className="card contract"><div className="card-head"><h3>Delivery contract</h3><span className="badge green-badge">GUARANTEED PATH</span></div><p><strong>At-least-once delivery with idempotent processing.</strong></p><p>Publisher confirms and consumer ACKs are intentionally separate from database transactions. Duplicate publication is expected in the crash window; inbox and connector idempotency make the side effect safe.</p><div className="contract-row"><span>Outbox</span><b>Atomic intent</b></div><div className="contract-row"><span>Broker</span><b>Durable + confirmed</b></div><div className="contract-row"><span>Consumer</span><b>Manual ACK</b></div></div></div></section></div></main>;
}
createRoot(document.getElementById('root')!).render(<App />);

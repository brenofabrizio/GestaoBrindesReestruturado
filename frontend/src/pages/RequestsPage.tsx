import { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, ChevronUp, ClipboardList, Plus, Send, X } from "lucide-react";
import { PageHeader } from "../components/Card";
import { Empty, StatusBadge } from "./DashboardPage";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import type { GiftRequest, Product } from "../types";

type CartLine = { product: string; quantity: number };

export function RequestsPage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<GiftRequest[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [product, setProduct] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [justification, setJustification] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [rejectReasons, setRejectReasons] = useState<Record<string, string>>({});
  const [fulfillAmounts, setFulfillAmounts] = useState<Record<string, Record<string, number>>>({});
  const [busyId, setBusyId] = useState("");
  const role = user?.profile.role || "";
  const canCreate = ["requester", "approver", "admin"].includes(role);
  const canProcess = ["operations", "operator", "approver", "admin"].includes(role);
  const canCancelAny = ["approver", "admin"].includes(role);
  const reload = () => Promise.all([api.requests(), api.products()]).then(([rows, items]) => { setRequests(rows); setProducts(items); });

  useEffect(() => { reload().catch((err) => setError(err.message)); }, []);
  const visibleRequests = useMemo(() => requests.filter((row) => {
    const term = search.toLowerCase();
    const matchesSearch = !term || `${row.id} ${row.justification} ${row.items.map((item) => products.find((p) => p.id === item.product)?.name || item.product).join(" ")}`.toLowerCase().includes(term);
    return matchesSearch && (!statusFilter || row.status === statusFilter);
  }), [requests, search, statusFilter, products]);

  function addToCart(event: React.FormEvent) {
    event.preventDefault();
    if (!product || quantity < 1) return;
    setCart((lines) => {
      const existing = lines.find((line) => line.product === product);
      if (existing) return lines.map((line) => line.product === product ? { ...line, quantity: line.quantity + quantity } : line);
      return [...lines, { product, quantity }];
    });
    setProduct("");
    setQuantity(1);
  }
  async function createRequest(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!cart.length) { setError("Adicione pelo menos um produto ao pedido."); return; }
    setBusyId("new");
    try {
      const created = await api.createRequest({ justification: justification.trim(), items: cart });
      await api.requestAction(created.id, "submit");
      setMessage("Solicitação enviada para análise.");
      setJustification("");
      setCart([]);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a solicitação.");
    } finally { setBusyId(""); }
  }
  async function action(id: string, name: string, body: unknown = {}) {
    setError("");
    setMessage("");
    setBusyId(id);
    try {
      await api.requestAction(id, name, body);
      setMessage("Ação concluída.");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ação não concluída.");
    } finally { setBusyId(""); }
  }

  function productName(id: string) { return products.find((item) => item.id === id)?.name || id; }
  function canCancel(request: GiftRequest) {
    return !["fulfilled", "rejected", "cancelled"].includes(request.status) && (request.requester === user?.id || canCancelAny);
  }

  return <section className="page">
    <PageHeader title="Solicitações" description="Acompanhe cada etapa, os itens, as aprovações e o atendimento." action={canCreate && <button className="primary-button" onClick={() => document.getElementById("new-request")?.scrollIntoView({ behavior: "smooth" })}><Plus size={16} />Nova solicitação</button>} />
    {error && <div className="alert error" role="alert">{error}</div>}
    {message && <div className="alert success" role="status">{message}</div>}
    <div className="request-grid">
      <div>
        <div className="toolbar"><input aria-label="Buscar solicitações" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por código, item ou justificativa" /><select aria-label="Filtrar por status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">Todos os status</option>{["draft", "submitted", "approved", "reserved", "partially_fulfilled", "fulfilled", "rejected", "cancelled"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></div>
        <div className="table-panel"><div className="panel-heading"><div><span className="eyebrow">Pipeline</span><h3>Solicitações</h3></div></div>
          {visibleRequests.length ? visibleRequests.map((request) => <div className="request-row request-card" key={request.id}>
            <div className="request-symbol"><ClipboardList size={17} /></div>
            <div className="row-main"><strong>#{request.id.slice(0, 8)}</strong><span>{request.items.map((item) => `${productName(item.product)} × ${item.quantity}`).join(", ")}</span><small>{request.justification || "Sem justificativa"}</small>
              {selectedId === request.id && <div className="request-detail"><h4>Itens e quantidades</h4>
                {request.items.map((item) => <div className="detail-line" key={item.id}><span>{productName(item.product)}</span><span>Solicitado {item.quantity} · Reservado {item.reserved_quantity} · Atendido {item.fulfilled_quantity}</span>{["reserved", "partially_fulfilled"].includes(request.status) && canProcess && <input aria-label={`Quantidade de ${productName(item.product)} para atender`} type="number" min="0" max={item.reserved_quantity} value={fulfillAmounts[request.id]?.[item.id] ?? 0} onChange={(event) => setFulfillAmounts({ ...fulfillAmounts, [request.id]: { ...fulfillAmounts[request.id], [item.id]: Number(event.target.value) } })} />}</div>)}
                {request.rejection_reason && <p className="rejection-reason">Motivo da rejeição: {request.rejection_reason}</p>}
                {canProcess && request.status === "submitted" && <div className="reject-form"><label>Motivo da rejeição<input value={rejectReasons[request.id] || ""} onChange={(event) => setRejectReasons({ ...rejectReasons, [request.id]: event.target.value })} placeholder="Obrigatório para rejeitar" /></label><button className="icon-button danger" disabled={(rejectReasons[request.id] || "").trim().length < 3 || busyId === request.id} onClick={() => action(request.id, "reject", { reason: rejectReasons[request.id]?.trim() })}>Rejeitar</button></div>}
              </div>}
            </div>
            <div className="request-actions"><StatusBadge status={request.status} /><button className="icon-button" aria-label={selectedId === request.id ? "Fechar detalhes" : "Ver detalhes"} onClick={() => setSelectedId(selectedId === request.id ? "" : request.id)}>{selectedId === request.id ? <ChevronUp size={15} /> : <ChevronDown size={15} />}</button>
              {request.status === "draft" && <button className="icon-button" title="Enviar" disabled={busyId === request.id} onClick={() => action(request.id, "submit")}><Send size={15} /></button>}
              {request.status === "submitted" && canProcess && <button className="icon-button" title="Aprovar" disabled={busyId === request.id} onClick={() => action(request.id, "approve")}><Check size={15} /></button>}
              {request.status === "approved" && canProcess && <button className="icon-button" title="Reservar" disabled={busyId === request.id} onClick={() => action(request.id, "reserve")}><ClipboardList size={15} /></button>}
              {["reserved", "partially_fulfilled"].includes(request.status) && canProcess && <button className="small-button" disabled={busyId === request.id || !request.items.some((item) => (fulfillAmounts[request.id]?.[item.id] || 0) > 0)} onClick={() => action(request.id, "fulfill", { items: request.items.map((item) => ({ item_id: item.id, quantity: fulfillAmounts[request.id]?.[item.id] || 0 })) })}>Atender quantidades</button>}
              {canCancel(request) && <button className="icon-button danger" title="Cancelar" disabled={busyId === request.id} onClick={() => { if (window.confirm("Cancelar esta solicitação e liberar as reservas pendentes?")) void action(request.id, "cancel"); }}><X size={15} /></button>}
            </div>
          </div>) : <Empty text="Nenhuma solicitação encontrada." />}
        </div>
      </div>
      {canCreate && <div id="new-request" className="panel"><div className="panel-heading"><div><span className="eyebrow">Novo fluxo</span><h3>Criar solicitação</h3></div></div>
        <form onSubmit={addToCart} className="inline-form"><label>Brinde<select value={product} onChange={(event) => setProduct(event.target.value)} required><option value="">Selecione</option>{products.filter((item) => item.is_active && !cart.some((line) => line.product === item.id)).map((item) => <option key={item.id} value={item.id}>{item.sku} · {item.name}</option>)}</select></label><label>Quantidade<input type="number" min="1" step="1" value={quantity} onChange={(event) => setQuantity(Number(event.target.value))} required /></label><button className="secondary-button" type="submit"><Plus size={15} />Adicionar</button></form>
        {cart.length > 0 && <div className="cart-lines"><strong>Itens no pedido</strong>{cart.map((line) => <div className="detail-line" key={line.product}><span>{productName(line.product)} × {line.quantity}</span><button className="icon-button danger" type="button" aria-label={`Remover ${productName(line.product)}`} onClick={() => setCart(cart.filter((item) => item.product !== line.product))}><X size={14} /></button></div>)}</div>}
        <form onSubmit={createRequest}><label>Justificativa<textarea value={justification} onChange={(event) => setJustification(event.target.value)} placeholder="Qual é o objetivo desta solicitação?" rows={4} required /></label><button className="primary-button" type="submit" disabled={!cart.length || busyId === "new"}><Send size={16} />{busyId === "new" ? "Enviando..." : "Enviar para aprovação"}</button></form>
      </div>}
    </div>
  </section>;
}

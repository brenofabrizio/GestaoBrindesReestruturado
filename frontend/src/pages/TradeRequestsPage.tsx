import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type PointerEvent } from "react";
import { ClipboardCheck, Package, Plus, RefreshCw, Send, X } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { PageHeader } from "../components/Card";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { can, canAny } from "../lib/access";
import { validateTradeItemDraft } from "../lib/trade-validation";
import { clearWithdrawalAttempt, createWithdrawalAttempt } from "../lib/withdrawal-attempt";
import type { Industry, Product, TradeRequest, TradeRequestItemDraft } from "../types";

const STATUS_LABELS: Record<string, string> = {
  solicitada: "Aguardando aprovação",
  compra_realizada: "Compra aprovada",
  aguardando_recebimento: "Aguardando recebimento no CD",
  recebido_cd: "Recebido no CD",
  pronta: "Pronta para retirada",
  retirado: "Retirada parcial",
  entregue: "Entregue",
  reprovada: "Reprovada",
  cancelada: "Cancelada",
};

const ACTION_LABELS = {
  campanha: "Campanha",
  premiacao: "Premiação",
  evento: "Evento",
  feirao: "Feirão",
  outro: "Outro",
};

function SignaturePad({ onSignatureChange }: { onSignatureChange: (signature: string) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);

  function point(event: PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * canvas.width,
      y: ((event.clientY - rect.top) / rect.height) * canvas.height,
    };
  }

  function start(event: PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    const position = point(event);
    drawing.current = true;
    canvas.setPointerCapture(event.pointerId);
    context.beginPath();
    context.moveTo(position.x, position.y);
    context.lineWidth = 3;
    context.lineCap = "round";
    context.strokeStyle = "#14213d";
  }

  function draw(event: PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current) return;
    const context = canvasRef.current?.getContext("2d");
    if (!context) return;
    const position = point(event);
    context.lineTo(position.x, position.y);
    context.stroke();
    const canvas = canvasRef.current;
    if (canvas) onSignatureChange(canvas.toDataURL("image/png"));
  }

  function finish() {
    if (!drawing.current) return;
    drawing.current = false;
    const signature = canvasRef.current?.toDataURL("image/png") || "";
    onSignatureChange(signature);
  }

  function clear() {
    const canvas = canvasRef.current;
    canvas?.getContext("2d")?.clearRect(0, 0, canvas.width, canvas.height);
    onSignatureChange("");
  }

  return <div className="signature-pad">
    <canvas ref={canvasRef} width={640} height={180} aria-label="Assinatura de quem retirou"
      onPointerDown={start} onPointerMove={draw} onPointerUp={finish} onPointerCancel={finish} />
    <button className="secondary-button" type="button" onClick={clear}>Limpar assinatura</button>
  </div>;
}

export function TradeRequestsPage() {
  const { user } = useAuth();
  const canCreate = can(user, "requests.create");
  const canApprove = can(user, "requests.approve");
  const canReceive = canAny(user, ["stock.receive", "stock.entry"]);
  const canWithdraw = canAny(user, ["requests.process", "stock.exit", "events.withdraw", "stock.exit_confirm"]);
  const industryUser = user?.profile.role === "industry";
  const [requests, setRequests] = useState<TradeRequest[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [industryId, setIndustryId] = useState(user?.profile.industry || "");
  const [purpose, setPurpose] = useState("");
  const [recipient, setRecipient] = useState("");
  const [actionType, setActionType] = useState<TradeRequest["action_type"]>("campanha");
  const [deliveryPlace, setDeliveryPlace] = useState("CD Belford Roxo");
  const [selectedProduct, setSelectedProduct] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [unitValue, setUnitValue] = useState("0.00");
  const [itemDrafts, setItemDrafts] = useState<TradeRequestItemDraft[]>([]);
  const [busy, setBusy] = useState("");
  const [signatureByRequest, setSignatureByRequest] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const productNames = useMemo(() => new Map(products.map((product) => [product.id, product.name])), [products]);
  const industryNames = useMemo(() => new Map(industries.map((industry) => [industry.id, industry.name])), [industries]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [requestRows, productRows, industryRows] = await Promise.all([
        api.tradeRequests(),
        api.products(),
        api.industries(),
      ]);
      setRequests(requestRows);
      requestRows.forEach((tradeRequest) => clearWithdrawalAttempt(sessionStorage, tradeRequest.id));
      setProducts(productRows.filter((product) => product.is_active));
      setIndustries(industryRows.filter((industry) => industry.is_active));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar a fila TRADE.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!industryId) {
      setIndustryId(user?.profile.industry || industries[0]?.id || "");
    }
  }, [industryId, industries, user]);

  function addItem() {
    const validationError = validateTradeItemDraft(quantity, unitValue);
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!selectedProduct) {
      setError("Selecione um brinde antes de adicionar.");
      return;
    }
    if (itemDrafts.some((item) => item.product === selectedProduct)) {
      setError("O mesmo brinde não pode aparecer duas vezes.");
      return;
    }
    setError("");
    setItemDrafts((current) => [
      ...current,
      { product: selectedProduct, kind: "fisico", qty_requested: quantity, unit_value: unitValue || "0.00" },
    ]);
    setSelectedProduct("");
    setQuantity(1);
    setUnitValue("0.00");
  }

  async function createRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!industryId || !purpose.trim() || itemDrafts.length === 0) {
      setError("Informe a indústria, a finalidade e ao menos um brinde.");
      return;
    }
    setError("");
    setMessage("");
    setBusy("create");
    try {
      await api.createTradeRequest({
        industry_id: industryId,
        purpose: purpose.trim(),
        recipient: recipient.trim(),
        action_type: actionType,
        delivery_place: deliveryPlace.trim() || "CD Belford Roxo",
        items: itemDrafts,
      });
      setMessage("Solicitação TRADE enviada para aprovação.");
      setPurpose("");
      setRecipient("");
      setItemDrafts([]);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a solicitação.");
    } finally {
      setBusy("");
    }
  }

  async function approveRequest(event: FormEvent<HTMLFormElement>, tradeRequest: TradeRequest) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(tradeRequest.id);
    setError("");
    setMessage("");
    try {
      await api.approveTradeRequest(tradeRequest.id, {
        purchase_ticket_no: String(form.get("purchase_ticket_no") || "").trim(),
        notes: String(form.get("notes") || "").trim(),
      });
      setMessage(`${tradeRequest.public_code} aprovado; aguardando recebimento no CD.`);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível aprovar a solicitação.");
    } finally {
      setBusy("");
    }
  }

  async function rejectRequest(event: FormEvent<HTMLFormElement>, tradeRequest: TradeRequest) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(tradeRequest.id);
    setError("");
    setMessage("");
    try {
      await api.rejectTradeRequest(tradeRequest.id, String(form.get("reason") || "").trim());
      setMessage(`${tradeRequest.public_code} reprovada.`);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível reprovar a solicitação.");
    } finally {
      setBusy("");
    }
  }

  async function receiveRequest(event: FormEvent<HTMLFormElement>, tradeRequest: TradeRequest) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const items = tradeRequest.items
      .map((item) => ({ item_id: item.product, qty: Number(form.get(`qty-${item.id}`) || 0) }))
      .filter((item) => item.qty > 0);
    if (items.length === 0) {
      setError("Informe ao menos uma quantidade recebida.");
      return;
    }
    setBusy(tradeRequest.id);
    setError("");
    setMessage("");
    try {
      await api.receiveTradeRequest(tradeRequest.id, {
        invoice_no: String(form.get("invoice_no") || "").trim(),
        notes: String(form.get("notes") || "").trim(),
        items,
      });
      setMessage(`Recebimento registrado para ${tradeRequest.public_code}.`);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível registrar o recebimento.");
    } finally {
      setBusy("");
    }
  }

  async function withdrawRequest(event: FormEvent<HTMLFormElement>, tradeRequest: TradeRequest) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const signatureData = signatureByRequest[tradeRequest.id] || "";
    if (!signatureData) {
      setError("Colete a assinatura de quem está retirando.");
      return;
    }
    const items = tradeRequest.items
      .map((item) => ({ item_id: item.product, qty: Number(form.get(`withdraw-${item.id}`) || 0) }))
      .filter((item) => item.qty > 0);
    if (items.length === 0) {
      setError("Informe ao menos uma quantidade retirada.");
      return;
    }
    setBusy(tradeRequest.id);
    setError("");
    setMessage("");
    const payload = {
      public_code: String(form.get("public_code") || "").trim(),
      received_by_name: String(form.get("received_by_name") || "").trim(),
      received_by_document: String(form.get("received_by_document") || "").trim(),
      received_by_email: String(form.get("received_by_email") || "").trim(),
      received_by_phone: String(form.get("received_by_phone") || "").trim(),
      recipient: String(form.get("recipient") || tradeRequest.recipient || "").trim(),
      signature_data: signatureData,
      notes: String(form.get("withdrawal_notes") || "").trim(),
      items,
    };
    try {
      const idempotencyKey = await createWithdrawalAttempt(sessionStorage, tradeRequest.id, payload);
      const updated = await api.withdrawTradeRequest(tradeRequest.id, {
        ...payload,
        idempotency_key: idempotencyKey,
      });
      const delivery = updated.deliveries[0];
      setMessage(delivery ? `Protocolo ${delivery.code} registrado.` : `Retirada registrada para ${tradeRequest.public_code}.`);
      setSignatureByRequest((current) => { const next = { ...current }; delete next[tradeRequest.id]; return next; });
      clearWithdrawalAttempt(sessionStorage, tradeRequest.id);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível registrar a retirada.");
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="page-stack">
      <PageHeader
        title="Solicitações TRADE"
        description="Compra aprovada com chamado, recebimento no CD por NF e saldo por indústria."
        action={<button className="secondary-button" type="button" onClick={() => void reload()}><RefreshCw size={16} />Atualizar</button>}
      />
      {error && <div className="alert error" role="alert">{error}</div>}
      {message && <div className="alert success" role="status">{message}</div>}

      {canCreate && <div className="panel trade-create-panel">
        <div className="panel-heading"><div><span className="eyebrow">Nova compra</span><h3>Solicitar brinde TRADE</h3></div></div>
        <form onSubmit={createRequest} className="form-grid">
          <label>Indústria
            <select value={industryId} onChange={(event) => setIndustryId(event.target.value)} required disabled={industryUser}>
              <option value="">Selecione</option>
              {industries.map((industry) => <option key={industry.id} value={industry.id}>{industry.name}</option>)}
            </select>
          </label>
          <label>Finalidade
            <input value={purpose} onChange={(event) => setPurpose(event.target.value)} maxLength={255} required />
          </label>
          <label>Destinatário
            <input value={recipient} onChange={(event) => setRecipient(event.target.value)} maxLength={150} />
          </label>
          <label>Tipo de ação
            <select value={actionType} onChange={(event) => setActionType(event.target.value as TradeRequest["action_type"])}>
              {Object.entries(ACTION_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label>Local de entrega
            <input value={deliveryPlace} onChange={(event) => setDeliveryPlace(event.target.value)} maxLength={190} />
          </label>
          <div className="form-grid trade-item-picker">
            <label>Brinde
              <select value={selectedProduct} onChange={(event) => setSelectedProduct(event.target.value)}>
                <option value="">Selecione</option>
                {products.map((product) => <option key={product.id} value={product.id}>{product.sku} · {product.name}</option>)}
              </select>
            </label>
            <label>Quantidade
              <input type="number" min="1" step="1" value={quantity} onChange={(event) => setQuantity(Number(event.target.value))} />
            </label>
            <label>Valor unitário
              <input type="number" min="0" step="0.01" value={unitValue} onChange={(event) => setUnitValue(event.target.value)} />
            </label>
            <button className="secondary-button" type="button" onClick={addItem}><Plus size={16} />Adicionar brinde</button>
          </div>
          {itemDrafts.length > 0 && <div className="trade-draft-lines">
            {itemDrafts.map((item) => <div className="trade-draft-line" key={item.product}>
              <span>{productNames.get(item.product) || item.product}</span>
              <span>{item.qty_requested} un. · R$ {item.unit_value}</span>
              <button className="icon-button" type="button" aria-label="Remover brinde" onClick={() => setItemDrafts((current) => current.filter((line) => line.product !== item.product))}><X size={15} /></button>
            </div>)}
          </div>}
          <button className="primary-button" type="submit" disabled={busy === "create"}><Send size={16} />Enviar para aprovação</button>
        </form>
      </div>}

      <div className="panel-heading"><div><span className="eyebrow">Fluxo de compra</span><h3>Solicitações TRADE</h3></div></div>
      {loading ? <div className="loading-screen">Carregando solicitações TRADE...</div> : requests.length === 0 ?
        <div className="empty-state">Nenhuma solicitação TRADE para este perfil.</div> :
        <div className="trade-request-list">
          {requests.map((tradeRequest) => {
            const statusLabel = STATUS_LABELS[tradeRequest.status] || tradeRequest.status;
            const canApproveThis = canApprove && tradeRequest.status === "solicitada";
            const canReceiveThis = canReceive && ["compra_realizada", "aguardando_recebimento", "recebido_cd"].includes(tradeRequest.status);
            const canWithdrawThis = canWithdraw && ["pronta", "retirado"].includes(tradeRequest.status);
            return <article className="panel trade-request-card" key={tradeRequest.id}>
              <header className="trade-card-header">
                <div><span className={`status-pill status-${tradeRequest.status}`}>{statusLabel}</span><h3>{tradeRequest.purpose}</h3><p>{tradeRequest.public_code} · {industryNames.get(tradeRequest.industry_id) || "Indústria"}</p></div>
                <QRCodeSVG value={tradeRequest.public_code} size={76} title={`Código TRADE ${tradeRequest.public_code}`} />
              </header>
              <div className="trade-request-meta">
                <span><strong>Destinatário:</strong> {tradeRequest.recipient || "—"}</span>
                <span><strong>Ação:</strong> {ACTION_LABELS[tradeRequest.action_type]}</span>
                <span><strong>Local:</strong> {tradeRequest.delivery_place}</span>
                <span><strong>Chamado:</strong> {tradeRequest.purchase_ticket_no || "Aguardando aprovação"}</span>
                <span><strong>NF:</strong> {tradeRequest.invoice_no || "Pendente"}</span>
              </div>
              <div className="trade-lines">
                {tradeRequest.items.map((item) => <div className="trade-line" key={item.id}>
                  <span>{productNames.get(item.product) || item.product}</span>
                  <span>Pedido {item.qty_requested} · Recebido {item.qty_received} · Retirado {item.qty_delivered}</span>
                </div>)}
              </div>
              {canApproveThis && <div className="trade-actions">
                <form className="trade-action-form" onSubmit={(event) => void approveRequest(event, tradeRequest)}>
                  <label>Chamado de compra
                    <input name="purchase_ticket_no" maxLength={50} required placeholder="Ex.: COM-2026-123" />
                  </label>
                  <label>Observação
                    <input name="notes" maxLength={2000} placeholder="Opcional" />
                  </label>
                  <button className="primary-button" type="submit" disabled={busy === tradeRequest.id}><ClipboardCheck size={16} />Aprovar e enviar ao CD</button>
                </form>
                <form className="trade-action-form" onSubmit={(event) => void rejectRequest(event, tradeRequest)}>
                  <label>Motivo da reprovação
                    <input name="reason" minLength={3} maxLength={500} required />
                  </label>
                  <button className="secondary-button danger-button" type="submit" disabled={busy === tradeRequest.id}>Reprovar</button>
                </form>
              </div>}
              {canReceiveThis && <form className="trade-actions trade-receive-form" onSubmit={(event) => void receiveRequest(event, tradeRequest)}>
                <div className="form-grid">
                  <label>Número da NF
                    <input name="invoice_no" maxLength={60} defaultValue={tradeRequest.invoice_no} required />
                  </label>
                  <label>Observação do recebimento
                    <input name="notes" maxLength={1000} />
                  </label>
                </div>
                <div className="trade-receive-lines">
                  {tradeRequest.items.map((item) => <label key={item.id}>{productNames.get(item.product) || item.product} · faltam {Math.max(0, item.qty_requested - item.qty_received)}
                    <input type="number" name={`qty-${item.id}`} min="0" max={Math.max(0, item.qty_requested - item.qty_received)} defaultValue={Math.max(0, item.qty_requested - item.qty_received)} />
                  </label>)}
                </div>
                <button className="primary-button" type="submit" disabled={busy === tradeRequest.id}><Package size={16} />Registrar recebimento</button>
                <small>Esta tela registra o número da NF; armazenamento durável do arquivo da nota ainda não está integrado.</small>
              </form>}
              {canWithdrawThis && <form className="trade-actions trade-withdraw-form" onSubmit={(event) => void withdrawRequest(event, tradeRequest)}>
                <div className="form-grid">
                  <label>Escaneie o QR do pedido
                    <input name="public_code" maxLength={24} placeholder="Aponte o leitor para o QR exibido no pedido" required />
                  </label>
                  <label>Nome de quem retira
                    <input name="received_by_name" maxLength={150} required />
                  </label>
                  <label>Documento
                    <input name="received_by_document" maxLength={30} />
                  </label>
                  <label>E-mail
                    <input name="received_by_email" type="email" maxLength={190} />
                  </label>
                  <label>Telefone
                    <input name="received_by_phone" maxLength={30} />
                  </label>
                  <label>Destinatário
                    <input name="recipient" maxLength={150} defaultValue={tradeRequest.recipient} />
                  </label>
                </div>
                <div className="trade-receive-lines">
                  {tradeRequest.items.map((item) => {
                    const remaining = Math.max(0, item.qty_received - item.qty_delivered);
                    return <label key={item.id}>{productNames.get(item.product) || item.product} · disponíveis {remaining}
                      <input type="number" name={`withdraw-${item.id}`} min="0" max={remaining} defaultValue={remaining} />
                    </label>;
                  })}
                </div>
                <label>Assinatura de quem recebe
                  <SignaturePad onSignatureChange={(signature) => setSignatureByRequest((current) => ({ ...current, [tradeRequest.id]: signature }))} />
                </label>
                <label>Observações
                  <input name="withdrawal_notes" maxLength={1000} />
                </label>
                <button className="primary-button" type="submit" disabled={busy === tradeRequest.id || !signatureByRequest[tradeRequest.id]}><ClipboardCheck size={16} />Registrar retirada e protocolo</button>
              </form>}
              {tradeRequest.status === "pronta" && !canWithdrawThis && <div className="alert info-alert">Pronta para retirada. Apresente o QR no CD.</div>}
              {tradeRequest.deliveries.length > 0 && <div className="trade-delivery-list">
                <span className="eyebrow">Comprovantes de retirada</span>
                {tradeRequest.deliveries.map((delivery) => <div className="trade-delivery-record" key={delivery.id}>
                  <div><strong>{delivery.code}</strong><span>{delivery.received_by_name} · {new Date(delivery.created_at).toLocaleString("pt-BR")}</span><small>{delivery.signature_present ? "Assinatura registrada" : "Assinatura ausente"}</small></div>
                  <div>{delivery.items.map((item) => <p key={item.id}>{productNames.get(item.product) || item.product}: {item.quantity} un. · saldo após retirada {item.balance_after}</p>)}</div>
                </div>)}
              </div>}
              {tradeRequest.history.length > 0 && <details className="trade-history"><summary>Histórico do fluxo</summary>
                {tradeRequest.history.map((entry) => <p key={entry.id}>{new Date(entry.created_at).toLocaleString("pt-BR")} · {entry.from_status || "criada"} → {entry.to_status}{entry.comment ? ` · ${entry.comment}` : ""}</p>)}
              </details>}
            </article>;
          })}
        </div>}
    </section>
  );
}

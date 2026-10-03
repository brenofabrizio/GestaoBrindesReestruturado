import { useCallback, useEffect, useState } from "react";
import { ArrowDownToLine, ArrowUpFromLine, History, Plus } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { PageHeader } from "../components/Card";
import { useAuth } from "../context/AuthContext";
import { can, canAny, canViewStockMovementHistory } from "../lib/access";
import { hasScannedQrToken } from "../lib/exit-orders";
import { api } from "../lib/api";
import type { Industry, IndustryBalance, Product, StockBalance, StockExitOrder, StockLocation, StockMovement, StockPosition } from "../types";

export function InventoryPage() {
  const { user } = useAuth();
  const canRegisterEntry = can(user, "stock.entry");
  const canCreateExit = can(user, "stock.exit");
  const canConfirmExit = can(user, "stock.exit_confirm");
  const canReadExitOrders = canCreateExit || canConfirmExit;
  const isIndustryUser = user?.profile.role === "industry";
  const canTransfer = can(user, "stock.transfer");
  const canReadLocations = canAny(user, ["stock.transfer", "stock.entry", "stock.exit"]);
  const canViewMovementHistory = canViewStockMovementHistory(user);
  const canManageLocations = can(user, "stock.locations.manage");
  const [products, setProducts] = useState<Product[]>([]);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [industryBalances, setIndustryBalances] = useState<IndustryBalance[]>([]);
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [exitOrders, setExitOrders] = useState<StockExitOrder[]>([]);
  const [locations, setLocations] = useState<StockLocation[]>([]);
  const [positions, setPositions] = useState<StockPosition[]>([]);
  const [entryProduct, setEntryProduct] = useState("");
  const [entryIndustry, setEntryIndustry] = useState("");
  const [entryLocation, setEntryLocation] = useState("");
  const [entryQuantity, setEntryQuantity] = useState(1);
  const [exitProduct, setExitProduct] = useState("");
  const [exitIndustry, setExitIndustry] = useState("");
  const [exitQuantity, setExitQuantity] = useState(1);
  const [exitNote, setExitNote] = useState("");
  const [exitLocation, setExitLocation] = useState("");
  const [transferProduct, setTransferProduct] = useState("");
  const [transferIndustry, setTransferIndustry] = useState("");
  const [transferQuantity, setTransferQuantity] = useState(1);
  const [transferFrom, setTransferFrom] = useState("");
  const [transferTo, setTransferTo] = useState("");
  const [transferNotes, setTransferNotes] = useState("");
  const [newLocationName, setNewLocationName] = useState("");
  const [newLocationKind, setNewLocationKind] = useState<StockLocation["kind"]>("other");
  const [busyOrder, setBusyOrder] = useState("");
  const [scannedExitToken, setScannedExitToken] = useState("");
  const [showAllMovements, setShowAllMovements] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const reload = useCallback(async () => {
    const [nextProducts, nextIndustries, nextIndustryBalances, nextBalances, nextMovements, nextOrders, nextLocations, nextPositions] = await Promise.all([
      api.products(),
      api.industries(),
      api.industryBalances(),
      isIndustryUser ? Promise.resolve([]) : api.balances(),
      canViewMovementHistory ? api.movements() : Promise.resolve([]),
      canReadExitOrders ? api.exitOrders() : Promise.resolve([]),
      canReadLocations ? api.locations() : Promise.resolve([]),
      canTransfer ? api.positions() : Promise.resolve([]),
    ]);
    setProducts(nextProducts);
    setIndustries(nextIndustries);
    setIndustryBalances(nextIndustryBalances);
    setBalances(nextBalances);
    setMovements(nextMovements);
    setExitOrders(nextOrders);
    setLocations(nextLocations);
    setPositions(nextPositions);
  }, [canReadExitOrders, canReadLocations, canTransfer, canViewMovementHistory, isIndustryUser]);

  useEffect(() => {
    const activeLocations = locations.filter((location) => location.is_active);
    const cdId = activeLocations.find((location) => location.kind === "cd")?.id || activeLocations[0]?.id || "";
    const otherId = activeLocations.find((location) => location.id !== cdId)?.id || "";
    if (!entryLocation && cdId) setEntryLocation(cdId);
    if (!exitLocation && cdId) setExitLocation(cdId);
    if (!transferFrom && cdId) setTransferFrom(cdId);
    if (!transferTo && otherId) setTransferTo(otherId);
    if (!transferIndustry && industries[0]) setTransferIndustry(industries[0].id);
  }, [entryLocation, exitLocation, industries, locations, transferFrom, transferIndustry, transferTo]);

  useEffect(() => {
    void reload().catch((err) => setError(err.message));
  }, [reload]);

  async function addEntry(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await api.createMovement({ product: entryProduct, industry: entryIndustry || null, location: entryLocation || null, movement_type: "entry", quantity_delta: entryQuantity });
      setMessage("Entrada registrada com sucesso.");
      setEntryQuantity(1);
      setEntryIndustry("");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível registrar a entrada.");
    }
  }

  async function createExit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const order = await api.createExitOrder({ product: exitProduct, quantity: exitQuantity, note: exitNote.trim(), industry: exitIndustry || undefined, location: exitLocation || undefined });
      setMessage(`Saída ${order.id.slice(0, 8)} autorizada e reservada; aguarda confirmação do CD.`);
      setExitQuantity(1);
      setExitNote("");
      setExitIndustry("");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a ordem de saída.");
    }
  }

  async function cancelPendingExit(order: StockExitOrder) {
    if (!canCreateExit || !window.confirm(`Cancelar a ordem de saída de ${order.quantity} unidade(s)?`)) return;
    setError("");
    setMessage("");
    setBusyOrder(order.id);
    try {
      await api.cancelExitOrder(order.id);
      setMessage("Ordem cancelada; quantidade liberada de volta ao disponível.");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível cancelar a saída.");
    } finally {
      setBusyOrder("");
    }
  }

  async function confirmScannedExit(event: React.FormEvent) {
    event.preventDefault();
    if (!canConfirmExit || !hasScannedQrToken(scannedExitToken)) {
      setError("Leia o QR de uma saída pendente antes de confirmar.");
      return;
    }
    if (!window.confirm("Confirmar a saída? O saldo será baixado agora.")) return;
    setError("");
    setMessage("");
    setBusyOrder("scanned-qr");
    try {
      const order = await api.confirmExitByQr(scannedExitToken.trim());
      setMessage(`Saída ${order.id.slice(0, 8)} confirmada; saldo atualizado e movimento registrado.`);
      setScannedExitToken("");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "QR inválido ou saída não pendente.");
    } finally {
      setBusyOrder("");
    }
  }

  async function createTransfer(event: React.FormEvent) {
    event.preventDefault();
    if (!canTransfer || !transferProduct || !transferIndustry || !transferFrom || !transferTo || transferFrom === transferTo) {
      setError("Informe produto, indústria, quantidade e locais diferentes.");
      return;
    }
    setBusyOrder("transfer");
    setError("");
    setMessage("");
    try {
      await api.transferStock({
        product: transferProduct,
        industry_id: transferIndustry,
        quantity: transferQuantity,
        from_location_id: transferFrom,
        to_location_id: transferTo,
        notes: transferNotes.trim(),
      });
      setMessage("Transferência registrada; o saldo global foi preservado.");
      setTransferQuantity(1);
      setTransferNotes("");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível transferir o estoque.");
    } finally {
      setBusyOrder("");
    }
  }

  async function createLocation(event: React.FormEvent) {
    event.preventDefault();
    if (!canManageLocations || !newLocationName.trim()) return;
    setBusyOrder("location");
    setError("");
    setMessage("");
    try {
      await api.createLocation({ name: newLocationName.trim(), kind: newLocationKind });
      setNewLocationName("");
      setMessage("Local de estoque cadastrado.");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível cadastrar o local.");
    } finally {
      setBusyOrder("");
    }
  }

  const industryTotal = industryBalances.reduce((sum, item) => sum + item.quantity, 0);
  const total = isIndustryUser ? industryTotal : balances.reduce((sum, item) => sum + item.quantity, 0);
  const available = balances.reduce((sum, item) => sum + item.available_quantity, 0);
  const reserved = balances.reduce((sum, item) => sum + item.reserved_quantity, 0);
  const pendingOrders = exitOrders.filter((order) => order.status === "pending");

  return (
    <section className="page">
      <PageHeader title="Estoque" description={isIndustryUser ? "Consulte somente os saldos atribuídos à sua indústria." : "Veja saldos físicos, reservas e o histórico de movimentações."} action={canViewMovementHistory ? <button className="secondary-button" type="button" onClick={() => setShowAllMovements((visible) => !visible)}><History size={16} />{showAllMovements ? "Ver recentes" : "Livro completo"}</button> : undefined} />
      {error && <div className="alert error" role="alert">{error}</div>}
      {message && <div className="alert success" role="status">{message}</div>}

      <div className="inventory-grid">
        {canRegisterEntry && <div className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Operação rápida</span><h3>Registrar entrada</h3></div><ArrowDownToLine size={20} className="icon-green" /></div>
          <form onSubmit={addEntry} className="inline-form">
            <label>Produto<select value={entryProduct} onChange={(event) => setEntryProduct(event.target.value)} required><option value="">Selecione</option>{products.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.sku} · {item.name}</option>)}</select></label>
            <label>Local<select value={entryLocation} onChange={(event) => setEntryLocation(event.target.value)} required><option value="">Selecione</option>{locations.filter((location) => location.is_active).map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label>
            <label>Indústria (opcional)<select value={entryIndustry} onChange={(event) => setEntryIndustry(event.target.value)}><option value="">Sem atribuição</option>{industries.filter((industry) => industry.is_active).map((industry) => <option key={industry.id} value={industry.id}>{industry.name}</option>)}</select></label>
            <label>Quantidade<input type="number" min="1" step="1" value={entryQuantity} onChange={(event) => setEntryQuantity(Number(event.target.value))} required /></label>
            <button className="primary-button" type="submit"><Plus size={16} />Registrar entrada</button>
          </form>
        </div>}

        {canCreateExit && <div className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Autorização</span><h3>Registrar saída pendente</h3></div><ArrowUpFromLine size={20} className="icon-violet" /></div>
          <p>A quantidade ficará reservada. O saldo físico só será baixado quando o CD confirmar.</p>
          <form onSubmit={createExit} className="inline-form">
            <label>Produto<select value={exitProduct} onChange={(event) => setExitProduct(event.target.value)} required><option value="">Selecione</option>{products.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.sku} · {item.name}</option>)}</select></label>
            <label>Local<select value={exitLocation} onChange={(event) => setExitLocation(event.target.value)} required><option value="">Selecione</option>{locations.filter((location) => location.is_active).map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label>
            <label>Indústria (opcional)<select value={exitIndustry} onChange={(event) => setExitIndustry(event.target.value)}><option value="">Sem atribuição</option>{industries.filter((industry) => industry.is_active).map((industry) => <option key={industry.id} value={industry.id}>{industry.name}</option>)}</select></label>
            <label>Quantidade<input type="number" min="1" step="1" value={exitQuantity} onChange={(event) => setExitQuantity(Number(event.target.value))} required /></label>
            <label>Finalidade/motivo<input value={exitNote} onChange={(event) => setExitNote(event.target.value)} maxLength={1000} required /></label>
            <button className="primary-button" type="submit"><Plus size={16} />Autorizar saída</button>
          </form>
        </div>}

        {canTransfer && <div className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Movimentação interna</span><h3>Transferir entre locais</h3></div></div>
          <p>Transferência muda a posição física; não é saída nem altera o saldo total do produto.</p>
          <form onSubmit={createTransfer} className="form-grid">
            <label>Produto<select value={transferProduct} onChange={(event) => setTransferProduct(event.target.value)} required><option value="">Selecione</option>{products.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.sku} · {item.name}</option>)}</select></label>
            <label>Indústria<select value={transferIndustry} onChange={(event) => setTransferIndustry(event.target.value)} required><option value="">Selecione</option>{industries.filter((industry) => industry.is_active).map((industry) => <option key={industry.id} value={industry.id}>{industry.name}</option>)}</select></label>
            <label>Origem<select value={transferFrom} onChange={(event) => setTransferFrom(event.target.value)} required><option value="">Selecione</option>{locations.filter((location) => location.is_active).map((location) => <option key={location.id} value={location.id}>{location.name} · {location.kind}</option>)}</select></label>
            <label>Destino<select value={transferTo} onChange={(event) => setTransferTo(event.target.value)} required><option value="">Selecione</option>{locations.filter((location) => location.is_active).map((location) => <option key={location.id} value={location.id}>{location.name} · {location.kind}</option>)}</select></label>
            <label>Quantidade<input type="number" min="1" step="1" value={transferQuantity} onChange={(event) => setTransferQuantity(Number(event.target.value))} required /></label>
            <label>Observações<input value={transferNotes} onChange={(event) => setTransferNotes(event.target.value)} maxLength={1000} /></label>
            <button className="primary-button" type="submit" disabled={busyOrder === "transfer" || !transferFrom || !transferTo || transferFrom === transferTo}>{busyOrder === "transfer" ? "Transferindo…" : "Registrar transferência"}</button>
          </form>
        </div>}

        {canManageLocations && <div className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Administração</span><h3>Cadastrar local de estoque</h3></div></div>
          <form onSubmit={createLocation} className="inline-form">
            <label>Nome<input value={newLocationName} onChange={(event) => setNewLocationName(event.target.value)} maxLength={120} required /></label>
            <label>Tipo<select value={newLocationKind} onChange={(event) => setNewLocationKind(event.target.value as StockLocation["kind"])}><option value="cd">CD / depósito</option><option value="event">Evento / feirão</option><option value="other">Outro local</option></select></label>
            <button className="secondary-button" type="submit" disabled={busyOrder === "location"}>{busyOrder === "location" ? "Salvando…" : "Cadastrar local"}</button>
          </form>
        </div>}

        <div className="panel">
          <div className="panel-heading"><div><span className="eyebrow">Resumo</span><h3>{isIndustryUser ? "Saldo da sua indústria" : "Distribuição do saldo"}</h3></div><ArrowUpFromLine size={20} className="icon-violet" /></div>
          <div className="stock-summary">
            {isIndustryUser ? <><strong>{total}</strong><span>unidades atribuídas à sua indústria</span><small>{industryBalances.length} produtos com movimento</small></> : <><strong>{total}</strong><span>unidades no estoque físico</span><div className="stock-bar"><span style={{ width: `${Math.min(100, (available / Math.max(1, total)) * 100)}%` }} /></div><small>{reserved} reservadas · {available} disponíveis</small></>}
          </div>
        </div>
      </div>

      {canReadExitOrders && <div className="table-panel">
        <div className="panel-heading"><div><span className="eyebrow">Confirmação do CD</span><h3>Saídas pendentes</h3></div></div>
        {canConfirmExit && <form onSubmit={confirmScannedExit} className="inline-form">
          <label>Leia o QR da retirada autorizada<input type="text" value={scannedExitToken} onChange={(event) => setScannedExitToken(event.target.value)} placeholder="Aponte o leitor QR para este campo" autoComplete="off" required /></label>
          <button className="primary-button" type="submit" disabled={!hasScannedQrToken(scannedExitToken) || busyOrder === "scanned-qr"}>{busyOrder === "scanned-qr" ? "Confirmando…" : "Confirmar QR"}</button>
        </form>}
        {pendingOrders.length === 0 ? <p>Nenhuma saída aguardando confirmação.</p> : <table>
          <thead><tr><th>Produto</th><th>Quantidade</th><th>Motivo</th>{canCreateExit && <><th>Indústria</th><th>QR para o solicitante</th><th>Token</th><th>Ação</th></>}</tr></thead>
          <tbody>{pendingOrders.map((order) => <tr key={order.id}>
            <td>{products.find((item) => item.id === order.product)?.name || order.product}</td><td>{order.quantity}</td><td>{order.note || "—"}</td>
            {canCreateExit && <><td>{industries.find((industry) => industry.id === order.industry)?.name || "—"}</td><td>{order.qr_token && <QRCodeSVG value={order.qr_token} size={72} title={`QR da saída ${order.id}`} />}</td><td><code>{order.qr_token || "—"}</code></td><td><button className="small-button" disabled={busyOrder === order.id} onClick={() => void cancelPendingExit(order)}>{busyOrder === order.id ? "Cancelando…" : "Cancelar ordem"}</button></td></>}
          </tr>)}</tbody>
        </table>}
      </div>}

      {!isIndustryUser && <div className="table-panel">
        <div className="panel-heading"><div><span className="eyebrow">Saldos atuais</span><h3>Por produto</h3></div></div>
        <table><thead><tr><th>Produto</th><th>Total</th><th>Reservado</th><th>Disponível</th></tr></thead>
          <tbody>{balances.map((balance) => { const item = products.find((productRow) => productRow.id === balance.product); return <tr key={balance.id}><td>{item ? `${item.sku} · ${item.name}` : balance.product}</td><td>{balance.quantity}</td><td>{balance.reserved_quantity}</td><td><strong className={balance.available_quantity === 0 ? "danger-text" : "green-text"}>{balance.available_quantity}</strong></td></tr>; })}</tbody>
        </table>
      </div>}

      {!isIndustryUser && <div className="table-panel">
        <div className="panel-heading"><div><span className="eyebrow">Posições</span><h3>Saldo por local</h3></div></div>
        {positions.length === 0 ? <p>Nenhuma posição registrada por local.</p> : <table>
          <thead><tr><th>Produto</th><th>Local</th><th>Tipo</th><th>Quantidade</th></tr></thead>
          <tbody>{positions.map((position) => <tr key={position.id}><td>{position.product.sku} · {position.product.name}</td><td>{position.location.name}</td><td>{position.location.kind}</td><td>{position.quantity}</td></tr>)}</tbody>
        </table>}
      </div>}

      <div className="table-panel">
        <div className="panel-heading"><div><span className="eyebrow">Estoque por indústria</span><h3>Saldo atribuído por produto</h3></div></div>
        {industryBalances.length === 0 ? <p>Nenhum movimento de estoque atribuído às indústrias visíveis para este perfil.</p> : <table>
          <thead><tr><th>Indústria</th><th>SKU</th><th>Produto</th><th>Saldo atribuído</th></tr></thead>
          <tbody>{industryBalances.map((row) => <tr key={`${row.industry_id}-${row.product_id}`}><td>{row.industry_name}</td><td>{row.sku}</td><td>{row.product_name}</td><td>{row.quantity}</td></tr>)}</tbody>
        </table>}
      </div>

      {canViewMovementHistory && <div className="table-panel">
        <div className="panel-heading"><div><span className="eyebrow">Histórico</span><h3>Últimas movimentações</h3></div></div>
        <table><thead><tr><th>Produto</th><th>Indústria</th><th>Tipo</th><th>Variação</th><th>Referência</th></tr></thead>
          <tbody>{(showAllMovements ? movements : movements.slice(0, 10)).map((movement) => <tr key={movement.id}><td>{products.find((item) => item.id === movement.product)?.name || movement.product}</td><td>{industries.find((industry) => industry.id === movement.industry)?.name || "—"}</td><td>{movement.movement_type}</td><td className={movement.quantity_delta > 0 ? "green-text" : "danger-text"}>{movement.quantity_delta > 0 ? "+" : ""}{movement.quantity_delta}</td><td>{movement.reference || "—"}</td></tr>)}</tbody>
        </table>
      </div>}
    </section>
  );
}

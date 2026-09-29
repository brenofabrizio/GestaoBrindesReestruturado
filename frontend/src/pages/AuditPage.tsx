import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Search, ShieldCheck } from "lucide-react";
import { PageHeader } from "../components/Card";
import { api } from "../lib/api";
import type { AuditEvent, Page } from "../types";

const emptyPage: Page<AuditEvent> = { count: 0, next: null, previous: null, results: [] };
const formatDate = (value: string) => new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
}).format(new Date(value));

export function AuditPage() {
  const [data, setData] = useState(emptyPage);
  const [filters, setFilters] = useState({ action: "", entity_type: "", actor: "", date_from: "", date_to: "" });
  const [applied, setApplied] = useState(filters);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let current = true;
    setLoading(true);
    api.audit(applied, page)
      .then((result) => { if (current) { setData(result); setError(""); } })
      .catch((err) => { if (current) setError(err instanceof Error ? err.message : "Falha ao consultar auditoria."); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [applied, page]);

  function applyFilters(event: React.FormEvent) {
    event.preventDefault();
    setPage(1);
    setApplied({ ...filters });
  }

  return <section className="page">
    <PageHeader title="Auditoria" description="Eventos operacionais, atores e entidades registrados no sistema." />
    {error && <div className="alert error" role="alert">{error}</div>}
    <form className="panel" onSubmit={applyFilters}>
      <div className="panel-heading"><div><span className="eyebrow">Consulta protegida</span><h3>Filtrar eventos</h3></div><ShieldCheck size={20} /></div>
      <div className="filter-grid">
        <label>Ação<input value={filters.action} onChange={(event) => setFilters({ ...filters, action: event.target.value })} placeholder="ex.: orders.request" /></label>
        <label>Entidade<input value={filters.entity_type} onChange={(event) => setFilters({ ...filters, entity_type: event.target.value })} placeholder="ex.: catalog.product" /></label>
        <label>ID do ator<input value={filters.actor} onChange={(event) => setFilters({ ...filters, actor: event.target.value })} placeholder="UUID do usuário" /></label>
        <label>De<input type="date" value={filters.date_from} onChange={(event) => setFilters({ ...filters, date_from: event.target.value })} /></label>
        <label>Até<input type="date" value={filters.date_to} onChange={(event) => setFilters({ ...filters, date_to: event.target.value })} /></label>
      </div>
      <button className="primary-button" type="submit"><Search size={16} />Aplicar filtros</button>
    </form>
    <div className="toolbar" style={{ marginTop: 20 }}><span className="result-count">{data.count} eventos</span><span className="result-count">Página {page}</span></div>
    <div className="table-panel"><table><thead><tr><th>Data</th><th>Ator</th><th>Ação</th><th>Entidade</th><th>Referência</th><th>Detalhes</th></tr></thead>
      <tbody>{data.results.map((event) => <tr key={event.id}>
        <td>{formatDate(event.created_at)}</td>
        <td>{event.actor_email || event.actor || "Sistema"}</td>
        <td><code>{event.action}</code></td>
        <td>{event.entity_type}</td>
        <td><code>{event.entity_id}</code></td>
        <td><details><summary>Ver</summary><pre className="audit-metadata">{JSON.stringify(event.metadata, null, 2)}</pre>{event.request_id && <small>Request ID: {event.request_id}</small>}</details></td>
      </tr>)}</tbody></table>
      {loading ? <div className="empty-state">Carregando eventos...</div> : data.results.length === 0 && <div className="empty-state">Nenhum evento encontrado para esses filtros.</div>}
    </div>
    <div className="toolbar" style={{ justifyContent: "flex-end", gap: 10, marginTop: 16 }}>
      <button className="secondary-button" disabled={!data.previous || loading} onClick={() => setPage((value) => Math.max(1, value - 1))}><ChevronLeft size={16} />Anterior</button>
      <button className="secondary-button" disabled={!data.next || loading} onClick={() => setPage((value) => value + 1)}>Próxima<ChevronRight size={16} /></button>
    </div>
  </section>;
}

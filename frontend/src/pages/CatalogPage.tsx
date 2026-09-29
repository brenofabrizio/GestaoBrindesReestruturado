import { useEffect, useMemo, useState } from "react";
import { Boxes, Edit2, Plus, Search, X } from "lucide-react";
import { PageHeader } from "../components/Card";
import { api } from "../lib/api";
import type { Category, Product } from "../types";
import { useAuth } from "../context/AuthContext";
import { can } from "../lib/access";

type ProductForm = {
  sku: string;
  name: string;
  description: string;
  category: string;
  unit: string;
  minimum_stock: number;
};
const emptyForm: ProductForm = { sku: "", name: "", description: "", category: "", unit: "unidade", minimum_stock: 0 };

export function CatalogPage() {
  const { user } = useAuth();
  const canManage = can(user, "catalog.manage");
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [query, setQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("active");
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState<ProductForm>(emptyForm);
  const [formOpen, setFormOpen] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  async function reload() {
    const [productRows, categoryRows] = await Promise.all([api.products(), api.categories()]);
    setProducts(productRows);
    setCategories(categoryRows);
  }
  useEffect(() => { reload().catch((err) => setError(err.message)); }, []);

  const filtered = useMemo(() => products.filter((product) => {
    const matchesQuery = `${product.name} ${product.sku} ${product.description}`.toLowerCase().includes(query.toLowerCase());
    const matchesCategory = !categoryFilter || product.category === categoryFilter;
    const matchesStatus = statusFilter === "all" || product.is_active === (statusFilter === "active");
    return matchesQuery && matchesCategory && matchesStatus;
  }), [products, query, categoryFilter, statusFilter]);

  function startCreate() {
    setEditing(null);
    setForm(emptyForm);
    setError("");
    setFormOpen(true);
  }
  function startEdit(product: Product) {
    setEditing(product);
    setForm({ sku: product.sku, name: product.name, description: product.description, category: product.category || "", unit: product.unit, minimum_stock: product.minimum_stock });
    setError("");
    setFormOpen(true);
  }
  async function saveProduct(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    setSaving(true);
    const payload = { ...form, category: form.category || null, minimum_stock: Number(form.minimum_stock) };
    try {
      if (editing) await api.updateProduct(editing.id, payload);
      else await api.createProduct(payload);
      setMessage(editing ? "Produto atualizado." : "Produto cadastrado.");
      setFormOpen(false);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível salvar o produto.");
    } finally {
      setSaving(false);
    }
  }
  async function toggleActive(product: Product) {
    setError("");
    setMessage("");
    try {
      await api.updateProduct(product.id, { is_active: !product.is_active });
      setMessage(product.is_active ? "Produto desativado sem apagar o histórico." : "Produto reativado.");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível atualizar o produto.");
    }
  }

  return <section className="page">
    <PageHeader title="Catálogo" description="Cadastre, edite e desative brindes sem apagar o histórico." action={canManage && <button className="primary-button" onClick={startCreate}><Plus size={16} />Novo produto</button>} />
    {error && <div className="alert error" role="alert">{error}</div>}
    {message && <div className="alert success" role="status">{message}</div>}
    {formOpen && canManage && <form className="panel catalog-form" onSubmit={saveProduct}>
      <div className="panel-heading"><div><span className="eyebrow">{editing ? "Atualização" : "Novo cadastro"}</span><h3>{editing ? "Editar produto" : "Cadastrar produto"}</h3></div><button className="icon-button" type="button" aria-label="Fechar" onClick={() => setFormOpen(false)}><X size={16} /></button></div>
      <div className="filter-grid">
        <label>SKU<input required maxLength={80} value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} /></label>
        <label>Nome<input required maxLength={180} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>Categoria<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}><option value="">Sem categoria</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
        <label>Unidade<input required maxLength={30} value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })} /></label>
        <label>Estoque mínimo<input required type="number" min="0" step="1" value={form.minimum_stock} onChange={(event) => setForm({ ...form, minimum_stock: Number(event.target.value) })} /></label>
      </div>
      <label>Descrição<textarea rows={3} maxLength={4000} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <button className="primary-button" type="submit" disabled={saving}>{saving ? "Salvando..." : editing ? "Salvar alterações" : "Cadastrar produto"}</button>
    </form>}
    <div className="toolbar catalog-toolbar">
      <div className="search-field"><Search size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar nome, descrição ou SKU" /></div>
      <label>Categoria<select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}><option value="">Todas</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
      <label>Situação<select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="active">Ativos</option><option value="inactive">Inativos</option><option value="all">Todos</option></select></label>
      <span className="result-count">{filtered.length} itens</span>
    </div>
    <div className="table-panel"><table><thead><tr><th>Produto</th><th>SKU</th><th>Categoria</th><th>Unidade</th><th>Estoque mínimo</th><th>Status</th>{canManage && <th>Ações</th>}</tr></thead><tbody>
      {filtered.map((product) => <tr key={product.id}>
        <td><div className="table-primary"><div className="table-icon"><Boxes size={16} /></div><div><strong>{product.name}</strong><small>{product.description || "Sem descrição"}</small></div></div></td>
        <td><code>{product.sku}</code></td><td>{categories.find((item) => item.id === product.category)?.name || "—"}</td><td>{product.unit}</td><td>{product.minimum_stock}</td>
        <td><span className={product.is_active ? "badge active" : "badge inactive"}>{product.is_active ? "Ativo" : "Inativo"}</span></td>
        {canManage && <td><div className="request-actions"><button className="icon-button" aria-label={`Editar ${product.name}`} onClick={() => startEdit(product)}><Edit2 size={15} /></button><button className={product.is_active ? "small-button" : "icon-button"} onClick={() => toggleActive(product)}>{product.is_active ? "Desativar" : "Reativar"}</button></div></td>}
      </tr>)}
    </tbody></table>{!filtered.length && <div className="empty-state">Nenhum produto encontrado.</div>}</div>
  </section>;
}

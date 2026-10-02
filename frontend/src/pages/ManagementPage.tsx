import { useEffect, useMemo, useState } from "react";
import { Check, Pencil, Plus, Save, UserRoundCog, X } from "lucide-react";
import { PageHeader } from "../components/Card";
import { useAuth } from "../context/AuthContext";
import { can } from "../lib/access";
import { api } from "../lib/api";
import type { LookupType, Role, User } from "../types";

const roleLabels: Record<Role, string> = {
  admin: "Administrador", approver: "TRADE / Gestor", operations: "CD / Estoque",
  operator: "Operador", requester: "Solicitante", industry: "Indústria",
};
const lookupLabels: Record<LookupType, string> = {
  categories: "Categorias", departments: "Departamentos", industries: "Indústrias",
  locations: "Locais", suppliers: "Fornecedores",
};
const permissionOptions = [
  ["catalog.view", "Consultar catálogo"], ["catalog.manage", "Gerenciar catálogo"],
  ["stock.view", "Consultar estoque"], ["stock.entry", "Registrar entradas"],
  ["stock.exit", "Registrar saídas"], ["stock.adjust", "Ajustar estoque"],
  ["stock.transfer", "Transferir entre locais"], ["stock.exit_confirm", "Confirmar saídas do CD"],
  ["requests.create", "Criar solicitações"], ["requests.view_own", "Ver próprias solicitações"],
  ["requests.view_department", "Ver solicitações do departamento"], ["requests.view_all", "Ver todas as solicitações"],
  ["requests.approve", "Aprovar solicitações"], ["requests.process", "Processar e atender solicitações"],
  ["requests.cancel_any", "Cancelar solicitações de terceiros"], ["lookups.view", "Consultar cadastros auxiliares"],
  ["lookups.manage", "Gerenciar cadastros auxiliares"], ["users.manage", "Gerenciar usuários"],
  ["roles.manage", "Gerenciar permissões"], ["audit.view", "Consultar auditoria"],
  ["reports.view", "Consultar relatórios"], ["reports.export", "Exportar relatórios"],
  ["events.view", "Consultar eventos"], ["events.manage", "Gerenciar eventos"],
] as const;
type ManagementData = Awaited<ReturnType<typeof api.management>>;
type UserForm = { username: string; email: string; first_name: string; last_name: string; role: Role; department: string; phone: string; password: string; is_active: boolean };
const blankUser: UserForm = { username: "", email: "", first_name: "", last_name: "", role: "requester", department: "", phone: "", password: "", is_active: true };

export function ManagementPage() {
  const { user } = useAuth();
  const [data, setData] = useState<ManagementData | null>(null);
  const [section, setSection] = useState<"users" | "lookups" | "permissions">(() => can(user, "users.manage") ? "users" : can(user, "lookups.manage") ? "lookups" : "permissions");
  const [lookupType, setLookupType] = useState<LookupType>("categories");
  const [lookupName, setLookupName] = useState("");
  const [lookupId, setLookupId] = useState("");
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userForm, setUserForm] = useState<UserForm>(blankUser);
  const [role, setRole] = useState<Role>("requester");
  const [permissions, setPermissions] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const canUsers = can(user, "users.manage");
  const canLookups = can(user, "lookups.manage");
  const canRoles = can(user, "roles.manage");

  async function reload() {
    const result = await api.management();
    setData(result);
    setPermissions(result.rolePermissions[role] || []);
  }
  useEffect(() => { reload().catch((reason) => setError(reason instanceof Error ? reason.message : "Não foi possível carregar a gestão.")); }, []);
  useEffect(() => { setPermissions(data?.rolePermissions[role] || []); }, [role, data]);

  const rows = useMemo(() => data?.lookups[lookupType] || [], [data, lookupType]);
  const departments = data?.lookups.departments.filter((item) => item.is_active) || [];

  function beginEditUser(target: User) {
    setEditingUser(target);
    setUserForm({ username: target.username, email: target.email, first_name: target.first_name, last_name: target.last_name, role: target.profile.role, department: target.profile.department, phone: target.profile.phone, password: "", is_active: target.is_active !== false });
    setError("");
  }
  function beginNewUser() { setEditingUser(null); setUserForm(blankUser); setError(""); }

  async function submitUser(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      await api.saveUser({ ...userForm, id: editingUser?.id, password: userForm.password || undefined });
      await reload(); beginNewUser(); setMessage(editingUser ? "Usuário atualizado." : "Usuário criado.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar o usuário."); }
    finally { setBusy(false); }
  }

  async function submitLookup(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      await api.saveLookup(lookupType, { id: lookupId || undefined, name: lookupName });
      await reload(); setLookupName(""); setLookupId(""); setMessage("Cadastro salvo.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar o cadastro."); }
    finally { setBusy(false); }
  }

  async function toggleLookup(item: { id: string; name: string; is_active: boolean }) {
    try { await api.saveLookup(lookupType, { ...item, is_active: !item.is_active }); await reload(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível atualizar o cadastro."); }
  }

  async function savePermissions() {
    setBusy(true); setError(""); setMessage("");
    try { await api.saveRolePermissions(role, permissions); await reload(); setMessage(`Permissões de ${roleLabels[role]} atualizadas.`); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar as permissões."); }
    finally { setBusy(false); }
  }

  return <section className="page">
    <PageHeader title="Gestão do sistema" description="Usuários, cadastros auxiliares e permissões por perfil." action={<UserRoundCog size={21} />} />
    {error && <div className="alert error" role="alert">{error}</div>}
    {message && <div className="alert success" role="status">{message}</div>}
    <div className="section-tabs" role="tablist" aria-label="Seções de gestão">
      {canUsers && <button className={section === "users" ? "tab-button selected" : "tab-button"} onClick={() => setSection("users")}>Usuários</button>}
      {canLookups && <button className={section === "lookups" ? "tab-button selected" : "tab-button"} onClick={() => setSection("lookups")}>Cadastros auxiliares</button>}
      {canRoles && <button className={section === "permissions" ? "tab-button selected" : "tab-button"} onClick={() => setSection("permissions")}>Perfis e permissões</button>}
    </div>

    {section === "users" && canUsers && <div className="management-grid">
      <form className="panel" onSubmit={submitUser}>
        <div className="panel-heading"><div><span className="eyebrow">Acesso ao sistema</span><h3>{editingUser ? "Editar usuário" : "Novo usuário"}</h3></div>{editingUser && <button type="button" className="icon-button" aria-label="Cancelar edição" onClick={beginNewUser}><X size={15} /></button>}</div>
        <div className="form-grid">
          <label>Nome<input value={userForm.first_name} onChange={(event) => setUserForm({ ...userForm, first_name: event.target.value })} required /></label>
          <label>Sobrenome<input value={userForm.last_name} onChange={(event) => setUserForm({ ...userForm, last_name: event.target.value })} /></label>
          <label>Usuário<input value={userForm.username} onChange={(event) => setUserForm({ ...userForm, username: event.target.value })} required /></label>
          <label>E-mail<input type="email" value={userForm.email} onChange={(event) => setUserForm({ ...userForm, email: event.target.value })} required /></label>
          <label>Perfil<select value={userForm.role} onChange={(event) => setUserForm({ ...userForm, role: event.target.value as Role })}>{Object.entries(roleLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>Departamento<input list="management-departments" value={userForm.department} onChange={(event) => setUserForm({ ...userForm, department: event.target.value })} /><datalist id="management-departments">{departments.map((item) => <option key={item.id} value={item.name} />)}</datalist></label>
          <label>Telefone<input value={userForm.phone} onChange={(event) => setUserForm({ ...userForm, phone: event.target.value })} /></label>
          <label>{editingUser ? "Nova senha (opcional)" : "Senha inicial"}<input type="password" minLength={8} autoComplete="new-password" value={userForm.password} onChange={(event) => setUserForm({ ...userForm, password: event.target.value })} required={!editingUser} /></label>
        </div>
        {editingUser && <label className="check-label"><input type="checkbox" checked={userForm.is_active} onChange={(event) => setUserForm({ ...userForm, is_active: event.target.checked })} />Acesso ativo</label>}
        <button className="primary-button" type="submit" disabled={busy}><Save size={15} />Salvar usuário</button>
      </form>
      <div className="table-panel"><div className="panel-heading"><div><span className="eyebrow">Contas locais</span><h3>Usuários cadastrados</h3></div><button className="secondary-button" onClick={beginNewUser}><Plus size={15} />Novo</button></div>
        <table><thead><tr><th>Usuário</th><th>Perfil</th><th>Departamento</th><th>Status</th><th></th></tr></thead><tbody>{data?.users.map((item) => <tr key={item.id}><td><strong>{item.first_name} {item.last_name}</strong><small className="table-subtext">{item.email}</small></td><td>{roleLabels[item.profile.role]}</td><td>{item.profile.department || "—"}</td><td><span className={`badge ${item.is_active === false ? "inactive" : "active"}`}>{item.is_active === false ? "Inativo" : "Ativo"}</span></td><td><button className="icon-button" aria-label={`Editar ${item.email}`} onClick={() => beginEditUser(item)}><Pencil size={14} /></button></td></tr>)}</tbody></table>
      </div>
    </div>}

    {section === "lookups" && canLookups && <div className="management-grid">
      <div className="panel"><div className="panel-heading"><div><span className="eyebrow">Listas de referência</span><h3>{lookupLabels[lookupType]}</h3></div></div>
        <div className="lookup-selector">{(Object.keys(lookupLabels) as LookupType[]).map((type) => <button key={type} className={lookupType === type ? "lookup-chip selected" : "lookup-chip"} onClick={() => { setLookupType(type); setLookupName(""); setLookupId(""); }}>{lookupLabels[type]}</button>)}</div>
        <form className="inline-form lookup-form" onSubmit={submitLookup}><label>{lookupId ? "Editar nome" : "Novo nome"}<input value={lookupName} onChange={(event) => setLookupName(event.target.value)} required /></label><button className="primary-button" type="submit" disabled={busy}><Plus size={15} />Salvar</button></form>
        <div className="lookup-list">{rows.map((item) => <div className="lookup-row" key={item.id}><span className={item.is_active ? "" : "muted-line"}>{item.name}</span><div><button className="icon-button" aria-label={`Editar ${item.name}`} onClick={() => { setLookupId(item.id); setLookupName(item.name); }}><Pencil size={14} /></button><button className={item.is_active ? "small-button deactivate-button" : "small-button"} onClick={() => toggleLookup(item)}>{item.is_active ? "Desativar" : "Reativar"}</button></div></div>)}{rows.length === 0 && <p className="empty-state">Nenhum registro nesta lista.</p>}</div>
      </div>
      <div className="panel accent-panel"><span className="eyebrow">Dados de referência</span><h3>Cadastros reutilizados na operação</h3><p className="management-help">Categorias, departamentos, indústrias, locais de estoque e fornecedores ficam salvos neste navegador e podem ser usados como base para os próximos fluxos.</p><p className="management-help">Desativar mantém o registro e o histórico existente; ele deixa de ser oferecido em novos cadastros.</p></div>
    </div>}

    {section === "permissions" && canRoles && <div className="panel">
      <div className="panel-heading"><div><span className="eyebrow">Acesso por perfil</span><h3>Permissões configuráveis</h3></div></div>
      <div className="role-toolbar"><label>Perfil<select value={role} onChange={(event) => setRole(event.target.value as Role)}>{(Object.keys(roleLabels) as Role[]).filter((item) => item !== "admin").map((item) => <option key={item} value={item}>{roleLabels[item]}</option>)}</select></label><span className="result-count">As alterações são aplicadas a este navegador.</span></div>
      <div className="permission-grid">{permissionOptions.map(([permission, label]) => <label className="permission-option" key={permission}><input type="checkbox" checked={permissions.includes(permission)} onChange={(event) => setPermissions(event.target.checked ? [...permissions, permission] : permissions.filter((item) => item !== permission))} /><span>{label}</span></label>)}</div>
      <button className="primary-button" onClick={savePermissions} disabled={busy}><Check size={15} />Salvar permissões</button>
    </div>}
  </section>;
}

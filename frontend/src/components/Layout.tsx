import { BarChart3, Boxes, ClipboardList, LayoutDashboard, LogOut, Package, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { can } from "../lib/access";

const navigation = [
  { to: "/", label: "Visão geral", icon: LayoutDashboard },
  { to: "/catalog", label: "Catálogo", icon: Boxes },
  { to: "/inventory", label: "Estoque", icon: Package },
  { to: "/requests", label: "Solicitações", icon: ClipboardList },
  { to: "/audit", label: "Auditoria", icon: ShieldCheck },
];

export function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">GB</span><span>Gestão Brindes</span></div>
        <nav className="nav-list">
          {navigation.filter(({ to }) => to !== "/inventory" || can(user, "stock.view")).filter(({ to }) => to !== "/audit" || can(user, "audit.view")).map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
              <Icon size={18} />{label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="profile-mini"><div className="avatar">{user?.first_name?.[0] || user?.email[0]}</div><div><strong>{user?.first_name || user?.username}</strong><small>{user?.profile.role}</small></div></div>
          <button className="ghost-button" onClick={logout}><LogOut size={16} />Sair</button>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar"><div><span className="eyebrow">Operação</span><h1>Controle de brindes</h1></div><div className="topbar-status"><span className="status-dot" />Modo local · JSON</div></header>
        <Outlet />
      </main>
    </div>
  );
}

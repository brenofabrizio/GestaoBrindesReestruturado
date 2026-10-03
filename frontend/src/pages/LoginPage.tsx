import { useState } from "react";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível entrar.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-art">
        <div className="brand"><span className="brand-mark">GB</span><span>Gestão Brindes</span></div>
        <div className="login-message">
          <span className="eyebrow">Operação sem atrito</span>
          <h1>Seu estoque,<br /><em>em movimento.</em></h1>
          <p>Catálogo, solicitações e aprovações em um único lugar.</p>
        </div>
        <div className="login-art-footer">Controle operacional com rastreabilidade.</div>
      </div>
      <div className="login-panel">
        <div className="login-box">
          <div className="mobile-brand brand"><span className="brand-mark">GB</span><span>Gestão Brindes</span></div>
          <div className="login-icon"><LockKeyhole size={20} /></div>
          <span className="eyebrow">Autenticação API</span>
          <h2>Bem-vindo de volta</h2>
          <p className="muted">Entre com sua conta do sistema.</p>
          <form onSubmit={handleSubmit}>
            <label>E-mail<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="voce@empresa.com" required /></label>
            <label>Senha<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" required /></label>
            {error && <div className="alert error">{error}</div>}
            <button className="primary-button" disabled={busy}>
              {busy ? "Entrando..." : <>Entrar <ArrowRight size={17} /></>}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}

import { ShieldCheck } from "lucide-react";
import { PageHeader } from "../components/Card";

export function AuditPage() { return <section className="page"><PageHeader title="Auditoria" description="O histórico operacional completo ficará disponível para perfis autorizados." /><div className="panel empty-panel"><div className="login-icon"><ShieldCheck size={20} /></div><h3>Trilha protegida</h3><p>Os eventos já são registrados pelo backend. A consulta detalhada será conectada nesta tela após a definição do endpoint de filtros avançados.</p></div></section>; }


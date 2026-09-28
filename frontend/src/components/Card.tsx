import type { ReactNode } from "react";

export function Card({ title, value, detail, icon, tone = "blue" }: { title: string; value: string | number; detail: string; icon: ReactNode; tone?: string }) {
  return <div className={`metric-card ${tone}`}><div className="metric-icon">{icon}</div><div><span>{title}</span><strong>{value}</strong><small>{detail}</small></div></div>;
}

export function PageHeader({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="page-header"><div><span className="eyebrow">Módulo</span><h2>{title}</h2><p>{description}</p></div>{action}</div>;
}


import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useAuth } from "./context/AuthContext";
import { AuditPage } from "./pages/AuditPage";
import { CatalogPage } from "./pages/CatalogPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InventoryPage } from "./pages/InventoryPage";
import { LoginPage } from "./pages/LoginPage";
import { ManagementPage } from "./pages/ManagementPage";
import { RequestsPage } from "./pages/RequestsPage";

export function App() { const { user, loading } = useAuth(); if (loading) return <div className="loading-screen">Carregando operação...</div>; if (!user) return <LoginPage />; return <Routes><Route element={<Layout />}><Route path="/" element={<DashboardPage />} /><Route path="/catalog" element={<CatalogPage />} /><Route path="/inventory" element={<InventoryPage />} /><Route path="/requests" element={<RequestsPage />} /><Route path="/audit" element={<AuditPage />} /><Route path="/management" element={<ManagementPage />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes>; }

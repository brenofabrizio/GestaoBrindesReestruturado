import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useAuth } from "./context/AuthContext";
import { AuditPage } from "./pages/AuditPage";
import { CatalogPage } from "./pages/CatalogPage";
import { DashboardPage } from "./pages/DashboardPage";
import { InventoryPage } from "./pages/InventoryPage";
import { LoginPage } from "./pages/LoginPage";
import { RequestsPage } from "./pages/RequestsPage";
import { TradeRequestsPage } from "./pages/TradeRequestsPage";
import { requestCapabilities, canAny } from "./lib/access";

export function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Carregando operação...</div>;
  if (!user) return <LoginPage />;
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/trade" element={canAny(user, ["requests.create", "requests.view_own", "requests.view_department", "requests.view_all", "stock.receive", "stock.exit_confirm", "requests.process"]) ? <TradeRequestsPage /> : <Navigate to="/" replace />} />
        <Route
          path="/requests"
          element={requestCapabilities(user).canViewRequests ? <RequestsPage /> : <Navigate to="/" replace />}
        />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

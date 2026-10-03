import type { AuditEvent, Category, GiftRequest, Industry, IndustryBalance, Page, Product, StockBalance, StockExitOrder, StockLocation, StockMovement, StockPosition, StockTransfer, TradeRequest, TradeRequestItemDraft, User } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const ACCESS_KEY = "gestao_brindes_access";
const REFRESH_KEY = "gestao_brindes_refresh";

export const authStorage = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: { access: string; refresh: string }) {
    localStorage.setItem(ACCESS_KEY, tokens.access);
    localStorage.setItem(REFRESH_KEY, tokens.refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

async function parseResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || data?.message || "Não foi possível concluir a operação.";
    throw new Error(typeof message === "string" ? message : "Erro de validação.");
  }
  return data as T;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (authStorage.access) headers.set("Authorization", `Bearer ${authStorage.access}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401 && retry && authStorage.refresh) {
    const refreshed = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: authStorage.refresh }),
    });
    if (refreshed.ok) {
      const tokens = await refreshed.json();
      authStorage.set({ access: tokens.access, refresh: authStorage.refresh });
      return apiFetch<T>(path, options, false);
    }
    authStorage.clear();
  }
  return parseResponse<T>(response);
}

export const api = {
  login: (email: string, password: string) =>
    apiFetch<{ access: string; refresh: string }>("/auth/token/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => apiFetch<User>("/auth/me/"),
  industries: () => apiFetch<Industry[]>("/catalog/industries/"),
  products: () => apiFetch<Product[]>("/catalog/products/"),
  categories: () => apiFetch<Category[]>("/catalog/categories/"),
  createProduct: (payload: Partial<Product>) => apiFetch<Product>("/catalog/products/", {
    method: "POST",
    body: JSON.stringify(payload),
  }),
  updateProduct: (id: string, payload: Partial<Product>) => apiFetch<Product>(`/catalog/products/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }),
  balances: () => apiFetch<StockBalance[]>("/inventory/balances/"),
  locations: () => apiFetch<StockLocation[]>("/inventory/locations/"),
  createLocation: (payload: { name: string; kind: StockLocation["kind"]; description?: string }) =>
    apiFetch<StockLocation>("/inventory/locations/", { method: "POST", body: JSON.stringify(payload) }),
  positions: (filters: Record<string, string> = {}) => {
    const params = new URLSearchParams(filters);
    const query = params.toString();
    return apiFetch<StockPosition[]>(`/inventory/positions/${query ? `?${query}` : ""}`);
  },
  transfers: () => apiFetch<StockTransfer[]>("/inventory/transfers/"),
  transferStock: (payload: { product: string; industry_id: string; quantity: number; from_location_id: string; to_location_id: string; notes?: string }) =>
    apiFetch<StockTransfer>("/inventory/transfers/", { method: "POST", body: JSON.stringify(payload) }),
  industryBalances: () => apiFetch<IndustryBalance[]>("/inventory/industry-balances/"),
  movements: () => apiFetch<StockMovement[]>("/inventory/movements/"),
  exitOrders: () => apiFetch<StockExitOrder[]>("/inventory/exit-orders/"),
  createExitOrder: (payload: { product: string; quantity: number; note: string; industry?: string; location?: string }) =>
    apiFetch<StockExitOrder>("/inventory/exit-orders/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  cancelExitOrder: (id: string) =>
    apiFetch<StockExitOrder>(`/inventory/exit-orders/${id}/cancel/`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  confirmExitByQr: (qrToken: string) =>
    apiFetch<StockExitOrder>("/inventory/exit-orders/confirm-by-qr/", {
      method: "POST",
      body: JSON.stringify({ qr_token: qrToken }),
    }),
  createMovement: (payload: Partial<StockMovement>) =>
    apiFetch<StockMovement>("/inventory/movements/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requests: () => apiFetch<GiftRequest[]>("/orders/requests/"),
  createRequest: (payload: { justification: string; items: { product: string; quantity: number }[] }) =>
    apiFetch<GiftRequest>("/orders/requests/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  requestAction: (id: string, action: string, body: unknown = {}) =>
    apiFetch<GiftRequest>(`/orders/requests/${id}/${action}/`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  tradeRequests: () => apiFetch<TradeRequest[]>("/trade/requests/"),
  createTradeRequest: (payload: { industry_id: string; purpose: string; recipient?: string; action_type: string; delivery_place?: string; items: TradeRequestItemDraft[] }) =>
    apiFetch<TradeRequest>("/trade/requests/", { method: "POST", body: JSON.stringify(payload) }),
  approveTradeRequest: (id: string, payload: { purchase_ticket_no: string; notes?: string }) =>
    apiFetch<TradeRequest>(`/trade/requests/${id}/approve/`, { method: "POST", body: JSON.stringify(payload) }),
  rejectTradeRequest: (id: string, reason: string) =>
    apiFetch<TradeRequest>(`/trade/requests/${id}/reject/`, { method: "POST", body: JSON.stringify({ reason }) }),
  receiveTradeRequest: (id: string, payload: { invoice_no: string; items: { item_id: string; qty: number }[]; notes?: string }) =>
    apiFetch<TradeRequest>(`/trade/requests/${id}/receive/`, { method: "POST", body: JSON.stringify(payload) }),
  withdrawTradeRequest: (id: string, payload: { public_code: string; idempotency_key: string; received_by_name: string; received_by_document?: string; received_by_email?: string; received_by_phone?: string; recipient?: string; signature_data: string; notes?: string; items: { item_id: string; qty: number }[] }) =>
    apiFetch<TradeRequest>(`/trade/requests/${id}/withdraw/`, { method: "POST", body: JSON.stringify(payload) }),
  audit: (filters: Record<string, string>, page = 1) => {
    const params = new URLSearchParams({ ...filters, page: String(page) });
    return apiFetch<Page<AuditEvent>>(`/audit/events/?${params.toString()}`);
  },
};

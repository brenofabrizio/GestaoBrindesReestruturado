import type { AuditEvent, Category, GiftRequest, Page, Product, StockBalance, StockMovement, User } from "../types";

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
  movements: () => apiFetch<StockMovement[]>("/inventory/movements/"),
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
  audit: (filters: Record<string, string>, page = 1) => {
    const params = new URLSearchParams({ ...filters, page: String(page) });
    return apiFetch<Page<AuditEvent>>(`/audit/events/?${params.toString()}`);
  },
};


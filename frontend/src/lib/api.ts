import type { AuditEvent, Category, GiftRequest, LookupType, Page, Product, Role, StockBalance, StockMovement, User } from "../types";
import { localDb } from "./localStore";

const ACCESS_KEY = "gestao_brindes_local_access";

export const authStorage = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(ACCESS_KEY);
  },
  set(tokens: { access: string; refresh: string }) {
    localStorage.setItem(ACCESS_KEY, tokens.access);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localDb.logout();
  },
};

export const api = {
  login: async (email: string, password: string) => {
    const user = localDb.login(email, password);
    return { access: user.id, refresh: user.id };
  },
  me: async (): Promise<User> => localDb.me(),
  products: async (): Promise<Product[]> => localDb.products(),
  categories: async (): Promise<Category[]> => localDb.categories(),
  createProduct: async (payload: Partial<Product>): Promise<Product> => localDb.createProduct(payload),
  updateProduct: async (id: string, payload: Partial<Product>): Promise<Product> => localDb.updateProduct(id, payload),
  management: async () => localDb.management(),
  saveLookup: async (type: LookupType, payload: { id?: string; name: string; is_active?: boolean }) => localDb.saveLookup(type, payload),
  saveUser: async (payload: { id?: string; username: string; email: string; first_name: string; last_name: string; role: Role; department: string; phone?: string; password?: string; is_active?: boolean }) => localDb.saveUser(payload),
  saveRolePermissions: async (role: Role, permissions: string[]) => localDb.saveRolePermissions(role, permissions),
  balances: async (): Promise<StockBalance[]> => localDb.balances(),
  movements: async (): Promise<StockMovement[]> => localDb.movements(),
  createMovement: async (payload: Partial<StockMovement>): Promise<StockMovement> => localDb.createMovement(payload),
  requests: async (): Promise<GiftRequest[]> => localDb.requests(),
  createRequest: async (payload: { justification: string; items: { product: string; quantity: number }[] }): Promise<GiftRequest> => localDb.createRequest(payload),
  requestAction: async (id: string, action: string, body: unknown = {}): Promise<GiftRequest> => localDb.requestAction(id, action, body as { reason?: string; items?: { item_id: string; quantity: number }[] }),
  audit: async (filters: Record<string, string> = {}, page = 1): Promise<Page<AuditEvent>> => {
    const results = localDb.audit(filters);
    return { count: results.length, next: null, previous: page > 1 ? "local" : null, results };
  },
};

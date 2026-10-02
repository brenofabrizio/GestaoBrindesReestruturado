import seed from "../data/seed.json";
import type {
  AuditEvent,
  Category,
  GiftRequest,
  Product,
  Role,
  StockBalance,
  StockMovement,
  User,
} from "../types";

type LocalUser = User & { password: string };
type LocalDatabase = {
  users: LocalUser[];
  categories: Category[];
  products: Product[];
  balances: StockBalance[];
  movements: StockMovement[];
  requests: GiftRequest[];
  audit: AuditEvent[];
};

const DATABASE_KEY = "gestao_brindes_json_database_v1";
const SESSION_KEY = "gestao_brindes_local_user";

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function createId(prefix: string) {
  const uuid = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : Math.random().toString(36).slice(2);
  return `${prefix}-${uuid}`;
}

function seedDatabase(): LocalDatabase {
  return clone(seed as LocalDatabase);
}

function readDatabase(): LocalDatabase {
  const stored = localStorage.getItem(DATABASE_KEY);
  if (!stored) {
    const initial = seedDatabase();
    localStorage.setItem(DATABASE_KEY, JSON.stringify(initial));
    return initial;
  }
  try {
    return JSON.parse(stored) as LocalDatabase;
  } catch {
    const initial = seedDatabase();
    localStorage.setItem(DATABASE_KEY, JSON.stringify(initial));
    return initial;
  }
}

function writeDatabase(database: LocalDatabase) {
  localStorage.setItem(DATABASE_KEY, JSON.stringify(database));
}

function publicUser(user: LocalUser): User {
  const { password: _password, ...safeUser } = user;
  return clone(safeUser);
}

function currentUser(database: LocalDatabase) {
  const id = localStorage.getItem(SESSION_KEY);
  return database.users.find((user) => user.id === id) || null;
}

function addAudit(database: LocalDatabase, actor: LocalUser | null, action: string, entityType: string, entityId: string, metadata: Record<string, unknown> = {}) {
  database.audit.unshift({
    id: createId("audit"),
    actor: actor?.id || null,
    action,
    entity_type: entityType,
    entity_id: entityId,
    metadata,
    created_at: new Date().toISOString(),
  });
}

function recalculateBalance(balance: StockBalance) {
  balance.available_quantity = Math.max(0, balance.quantity - balance.reserved_quantity);
  balance.updated_at = new Date().toISOString();
}

export const localDb = {
  login(email: string, password: string) {
    const database = readDatabase();
    const user = database.users.find((item) => item.email.toLowerCase() === email.trim().toLowerCase() && item.password === password);
    if (!user) throw new Error("E-mail ou senha inválidos.");
    localStorage.setItem(SESSION_KEY, user.id);
    return publicUser(user);
  },

  logout() {
    localStorage.removeItem(SESSION_KEY);
  },

  me() {
    const user = currentUser(readDatabase());
    if (!user) throw new Error("Sessão expirada.");
    return publicUser(user);
  },

  products() {
    return clone(readDatabase().products);
  },

  updateProduct(id: string, payload: Partial<Product>) {
    const database = readDatabase();
    const actor = currentUser(database);
    if (!actor) throw new Error("Sessão expirada.");
    const product = database.products.find((item) => item.id === id);
    if (!product) throw new Error("Produto não encontrado.");
    if (payload.sku && database.products.some((item) => item.id !== id && item.sku.toLowerCase() === payload.sku?.trim().toLowerCase())) throw new Error("Este SKU já está cadastrado.");
    Object.assign(product, { ...payload, sku: payload.sku?.trim() || product.sku, name: payload.name?.trim() || product.name });
    addAudit(database, actor, "catalog.product_updated", "product", id, payload as Record<string, unknown>);
    writeDatabase(database);
    return clone(product);
  },

  categories() {
    return clone(readDatabase().categories.filter((category) => category.is_active));
  },

  createProduct(payload: Partial<Product>) {
    const database = readDatabase();
    const actor = currentUser(database);
    if (!actor) throw new Error("Sessão expirada.");
    if (!payload.sku?.trim() || !payload.name?.trim()) throw new Error("Informe SKU e nome do produto.");
    if (database.products.some((product) => product.sku.toLowerCase() === payload.sku?.trim().toLowerCase())) throw new Error("Este SKU já está cadastrado.");
    const product: Product = {
      id: createId("product"), sku: payload.sku.trim(), name: payload.name.trim(), description: payload.description || "",
      category: payload.category || null, unit: payload.unit || "unidade", minimum_stock: Number(payload.minimum_stock || 0), is_active: true,
    };
    database.products.push(product);
    database.balances.push({ id: createId("balance"), product: product.id, quantity: 0, reserved_quantity: 0, available_quantity: 0, updated_at: new Date().toISOString() });
    addAudit(database, actor, "catalog.product_created", "product", product.id, { sku: product.sku });
    writeDatabase(database);
    return clone(product);
  },

  balances() {
    return clone(readDatabase().balances);
  },

  movements() {
    return clone(readDatabase().movements);
  },

  createMovement(payload: Partial<StockMovement>) {
    const database = readDatabase();
    const actor = currentUser(database);
    if (!actor) throw new Error("Sessão expirada.");
    if (!payload.product || !payload.movement_type || !payload.quantity_delta) throw new Error("Preencha produto e quantidade.");
    const balance = database.balances.find((item) => item.product === payload.product) || {
      id: createId("balance"), product: payload.product, quantity: 0, reserved_quantity: 0, available_quantity: 0, updated_at: new Date().toISOString(),
    };
    if (!database.balances.includes(balance)) database.balances.push(balance);
    const delta = Number(payload.quantity_delta);
    if (balance.quantity + delta < balance.reserved_quantity || balance.quantity + delta < 0) throw new Error("A movimentação deixaria o estoque indisponível.");
    balance.quantity += delta;
    recalculateBalance(balance);
    const movement: StockMovement = {
      id: createId("movement"), product: payload.product, movement_type: payload.movement_type, quantity_delta: delta,
      reference: payload.reference || "Operação local", note: payload.note || "", created_at: new Date().toISOString(),
    };
    database.movements.unshift(movement);
    addAudit(database, actor, `stock.${payload.movement_type}`, "product", payload.product, { quantity_delta: delta });
    writeDatabase(database);
    return clone(movement);
  },

  requests() {
    const database = readDatabase();
    const user = currentUser(database);
    if (!user) throw new Error("Sessão expirada.");
    const role = user.profile.role as Role;
    const requests = role === "admin" || role === "approver" || role === "operator" || role === "operations"
      ? database.requests
      : database.requests.filter((request) => request.requester === user.id);
    return clone(requests);
  },

  createRequest(payload: { justification: string; items: { product: string; quantity: number }[] }) {
    const database = readDatabase();
    const actor = currentUser(database);
    if (!actor) throw new Error("Sessão expirada.");
    if (!payload.items.length || payload.items.some((item) => !item.product || item.quantity < 1)) throw new Error("Adicione ao menos um item válido.");
    const request: GiftRequest = {
      id: createId("request"), requester: actor.id, status: "draft", justification: payload.justification.trim(), rejection_reason: "", approved_by: null,
      items: payload.items.map((item) => ({ id: createId("request-item"), product: item.product, quantity: item.quantity, reserved_quantity: 0, fulfilled_quantity: 0, remaining_quantity: item.quantity })),
      created_at: new Date().toISOString(),
    };
    database.requests.unshift(request);
    addAudit(database, actor, "orders.request_created", "request", request.id);
    writeDatabase(database);
    return clone(request);
  },

  requestAction(id: string, action: string, body: { reason?: string; items?: { item_id: string; quantity: number }[] } = {}) {
    const database = readDatabase();
    const actor = currentUser(database);
    if (!actor) throw new Error("Sessão expirada.");
    const request = database.requests.find((item) => item.id === id);
    if (!request) throw new Error("Solicitação não encontrada.");
    if (action === "submit") {
      if (request.status !== "draft") throw new Error("Somente rascunhos podem ser enviados.");
      request.status = "submitted";
    } else if (action === "approve") {
      if (request.status !== "submitted") throw new Error("Somente solicitações enviadas podem ser aprovadas.");
      request.status = "approved";
      request.approved_by = actor.id;
    } else if (action === "reject") {
      if (!["submitted", "approved"].includes(request.status)) throw new Error("Esta solicitação não pode ser rejeitada.");
      request.status = "rejected";
      request.rejection_reason = body.reason || "Rejeitada na operação.";
    } else if (action === "reserve") {
      if (request.status !== "approved") throw new Error("Somente solicitações aprovadas podem ser reservadas.");
      request.items.forEach((item) => {
        const balance = database.balances.find((entry) => entry.product === item.product);
        const remaining = item.quantity - item.fulfilled_quantity;
        if (!balance || balance.available_quantity < remaining) throw new Error("Estoque insuficiente para reservar esta solicitação.");
        balance.reserved_quantity += remaining;
        recalculateBalance(balance);
        item.reserved_quantity += remaining;
      });
      request.status = "reserved";
    } else if (action === "fulfill") {
      if (!["reserved", "partially_fulfilled"].includes(request.status)) throw new Error("Somente solicitações reservadas podem ser atendidas.");
      request.items.forEach((item) => {
        const amount = body.items?.find((entry) => entry.item_id === item.id)?.quantity ?? item.remaining_quantity;
        if (amount < 0 || amount > item.remaining_quantity || item.reserved_quantity < amount) throw new Error("Quantidade de atendimento inválida.");
        if (!amount) return;
        const balance = database.balances.find((entry) => entry.product === item.product);
        if (!balance) throw new Error("Saldo não encontrado.");
        balance.quantity -= amount;
        balance.reserved_quantity -= amount;
        recalculateBalance(balance);
        item.reserved_quantity -= amount;
        item.fulfilled_quantity += amount;
        item.remaining_quantity = item.quantity - item.fulfilled_quantity;
        database.movements.unshift({ id: createId("movement"), product: item.product, movement_type: "exit", quantity_delta: -amount, reference: request.id, note: "Baixa por atendimento local", created_at: new Date().toISOString() });
      });
      request.status = request.items.every((item) => item.remaining_quantity === 0) ? "fulfilled" : "partially_fulfilled";
    } else if (action === "cancel") {
      if (["fulfilled", "rejected", "cancelled"].includes(request.status)) throw new Error("Esta solicitação não pode mais ser cancelada.");
      request.items.forEach((item) => {
        const balance = database.balances.find((entry) => entry.product === item.product);
        if (balance) { balance.reserved_quantity -= item.reserved_quantity; recalculateBalance(balance); }
        item.reserved_quantity = 0;
      });
      request.status = "cancelled";
    } else {
      throw new Error("Ação não suportada.");
    }
    addAudit(database, actor, `orders.request_${action}`, "request", request.id, body);
    writeDatabase(database);
    return clone(request);
  },

  audit(filters: Record<string, string> = {}) {
    const database = readDatabase();
    return clone(database.audit.filter((event) => {
      const actionMatches = !filters.action || event.action.includes(filters.action);
      const entityMatches = !filters.entity_type || event.entity_type.includes(filters.entity_type);
      const actorMatches = !filters.actor || event.actor === filters.actor;
      const date = event.created_at.slice(0, 10);
      const fromMatches = !filters.date_from || date >= filters.date_from;
      const toMatches = !filters.date_to || date <= filters.date_to;
      return actionMatches && entityMatches && actorMatches && fromMatches && toMatches;
    }));
  },

  reset() {
    localStorage.removeItem(DATABASE_KEY);
    localStorage.removeItem(SESSION_KEY);
  },
};

import seed from "../data/seed.json";
import type {
  AuditEvent,
  Category,
  GiftRequest,
  LookupRecord,
  LookupType,
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
  departments: LookupRecord[];
  industries: LookupRecord[];
  locations: LookupRecord[];
  suppliers: LookupRecord[];
  rolePermissions: Record<Role, string[]>;
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
    const parsed = JSON.parse(stored) as Partial<LocalDatabase>;
    const initial = seedDatabase();
    const database = { ...initial, ...parsed } as LocalDatabase;
    if (Object.keys(initial).some((key) => !Object.prototype.hasOwnProperty.call(parsed, key))) writeDatabase(database);
    return database;
  } catch {
    throw new Error("Os dados locais estão inválidos. Eles foram preservados; não limpe o armazenamento antes de tentar recuperá-los.");
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
  return database.users.find((user) => user.id === id && user.is_active !== false) || null;
}

function hasPermission(database: LocalDatabase, user: LocalUser | User | null, permission: string) {
  if (!user) return false;
  const permissions = database.rolePermissions?.[user.profile.role] || [];
  return permissions.includes("*") || permissions.includes(permission);
}

function requirePermission(database: LocalDatabase, actor: LocalUser | null, permission: string) {
  if (!actor) throw new Error("Sessão expirada.");
  if (!hasPermission(database, actor, permission)) throw new Error("Seu perfil não tem permissão para esta operação.");
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
    const user = database.users.find((item) => item.is_active !== false && item.email.toLowerCase() === email.trim().toLowerCase() && item.password === password);
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

  hasPermission(user: User | null, permission: string) {
    return hasPermission(readDatabase(), user, permission);
  },

  management() {
    const database = readDatabase();
    const actor = currentUser(database);
    if (!["users.manage", "lookups.manage", "roles.manage"].some((permission) => hasPermission(database, actor, permission))) {
      throw new Error("Seu perfil não tem acesso à gestão do sistema.");
    }
    return {
      users: hasPermission(database, actor, "users.manage") ? database.users.map(publicUser) : [],
      lookups: {
        categories: clone(database.categories),
        departments: clone(database.departments),
        industries: clone(database.industries),
        locations: clone(database.locations),
        suppliers: clone(database.suppliers),
      },
      rolePermissions: hasPermission(database, actor, "roles.manage") ? clone(database.rolePermissions) : {} as Record<Role, string[]>,
    };
  },

  saveLookup(type: LookupType, payload: { id?: string; name: string; is_active?: boolean }) {
    const database = readDatabase();
    const actor = currentUser(database);
    requirePermission(database, actor, "lookups.manage");
    const name = payload.name.trim();
    if (!name) throw new Error("Informe o nome do cadastro.");
    const rows = database[type] as LookupRecord[];
    const duplicate = rows.some((row) => row.id !== payload.id && row.name.toLocaleLowerCase() === name.toLocaleLowerCase());
    if (duplicate) throw new Error("Já existe um cadastro com esse nome.");
    let record = rows.find((row) => row.id === payload.id);
    const isNew = !record;
    if (record) Object.assign(record, { name, is_active: payload.is_active ?? record.is_active });
    else { record = { id: createId(type.slice(0, -1)), name, is_active: true }; rows.push(record); }
    addAudit(database, actor, isNew ? "lookups.record_created" : "lookups.record_updated", type, record.id, { name });
    writeDatabase(database);
    return clone(record);
  },

  saveUser(payload: { id?: string; username: string; email: string; first_name: string; last_name: string; role: Role; department: string; phone?: string; password?: string; is_active?: boolean }) {
    const database = readDatabase();
    const actor = currentUser(database);
    requirePermission(database, actor, "users.manage");
    const email = payload.email.trim().toLowerCase();
    if (!email || !payload.username.trim() || !payload.first_name.trim()) throw new Error("Informe nome, usuário e e-mail.");
    if (database.users.some((row) => row.id !== payload.id && row.email.toLowerCase() === email)) throw new Error("Este e-mail já está cadastrado.");
    if (database.users.some((row) => row.id !== payload.id && row.username.toLowerCase() === payload.username.trim().toLowerCase())) throw new Error("Este nome de usuário já está cadastrado.");
    let user = database.users.find((row) => row.id === payload.id);
    if (user?.id === actor?.id && payload.is_active === false) throw new Error("Não é possível desativar a própria conta durante a sessão.");
    if (!user && (!payload.password || payload.password.length < 8)) throw new Error("A senha inicial deve ter pelo menos 8 caracteres.");
    if (user) {
      Object.assign(user, {
        username: payload.username.trim(), email, first_name: payload.first_name.trim(), last_name: payload.last_name.trim(),
        profile: { ...user.profile, role: payload.role, department: payload.department.trim(), phone: payload.phone || "" },
        is_active: payload.is_active ?? user.is_active ?? true,
      });
      if (payload.password) user.password = payload.password;
    } else {
      user = {
        id: createId("user"), username: payload.username.trim(), email, first_name: payload.first_name.trim(), last_name: payload.last_name.trim(),
        password: payload.password!, is_active: payload.is_active ?? true,
        profile: { id: createId("profile"), role: payload.role, department: payload.department.trim(), phone: payload.phone || "" },
      };
      database.users.push(user);
    }
    addAudit(database, actor, payload.id ? "users.user_updated" : "users.user_created", "user", user.id, { email: user.email, role: user.profile.role });
    writeDatabase(database);
    return publicUser(user);
  },

  saveRolePermissions(role: Role, permissions: string[]) {
    const database = readDatabase();
    const actor = currentUser(database);
    requirePermission(database, actor, "roles.manage");
    if (role === "admin") throw new Error("As permissões do administrador são sempre completas.");
    database.rolePermissions[role] = [...new Set(permissions)];
    addAudit(database, actor, "roles.permissions_updated", "role", role, { permissions: database.rolePermissions[role] });
    writeDatabase(database);
    return clone(database.rolePermissions[role]);
  },

  updateProduct(id: string, payload: Partial<Product>) {
    const database = readDatabase();
    const actor = currentUser(database);
    requirePermission(database, actor, "catalog.manage");
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
    requirePermission(database, actor, "catalog.manage");
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
    const permissionByType = { entry: "stock.entry", exit: "stock.exit", adjustment: "stock.adjust" } as const;
    requirePermission(database, actor, permissionByType[payload.movement_type || "entry"]);
    if (!payload.product || !payload.movement_type || !Number.isInteger(payload.quantity_delta) || !payload.quantity_delta) throw new Error("Preencha produto e uma quantidade inteira diferente de zero.");
    if (!database.products.some((product) => product.id === payload.product)) throw new Error("O brinde informado não existe.");
    if (payload.movement_type === "entry" && payload.quantity_delta < 0) throw new Error("Uma entrada precisa aumentar o saldo.");
    if (payload.movement_type === "exit" && payload.quantity_delta > 0) throw new Error("Uma saída precisa reduzir o saldo.");
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
    const canViewAll = hasPermission(database, user, "requests.view_all");
    const canViewDepartment = hasPermission(database, user, "requests.view_department");
    const requests = canViewAll ? database.requests : canViewDepartment
      ? database.requests.filter((request) => database.users.find((candidate) => candidate.id === request.requester)?.profile.department === user.profile.department)
      : database.requests.filter((request) => request.requester === user.id);
    return clone(requests);
  },

  createRequest(payload: { justification: string; items: { product: string; quantity: number }[] }) {
    const database = readDatabase();
    const actor = currentUser(database);
    if (!actor) throw new Error("Sessão expirada.");
    requirePermission(database, actor, "requests.create");
    if (!payload.items.length || payload.items.some((item) => !item.product || !Number.isInteger(item.quantity) || item.quantity < 1 || !database.products.some((product) => product.id === item.product && product.is_active))) throw new Error("Adicione itens ativos com quantidades inteiras válidas.");
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
    const requester = database.users.find((candidate) => candidate.id === request.requester);
    const inDepartment = requester?.profile.department === actor.profile.department;
    const canViewRequest = request.requester === actor.id || hasPermission(database, actor, "requests.view_all") || (inDepartment && hasPermission(database, actor, "requests.view_department"));
    if (!canViewRequest) throw new Error("Solicitação não encontrada.");
    if (action === "submit") {
      if (request.requester !== actor.id) throw new Error("Somente o solicitante pode enviar este pedido.");
      if (request.status !== "draft") throw new Error("Somente rascunhos podem ser enviados.");
      if (!request.justification.trim()) throw new Error("Informe a justificativa antes de enviar.");
      request.status = "submitted";
    } else if (action === "approve") {
      requirePermission(database, actor, "requests.approve");
      if (request.status !== "submitted") throw new Error("Somente solicitações enviadas podem ser aprovadas.");
      request.status = "approved";
      request.approved_by = actor.id;
    } else if (action === "reject") {
      requirePermission(database, actor, "requests.approve");
      if (!["submitted", "approved"].includes(request.status)) throw new Error("Esta solicitação não pode ser rejeitada.");
      if ((body.reason || "").trim().length < 3) throw new Error("Informe um motivo para rejeitar a solicitação.");
      request.status = "rejected";
      request.rejection_reason = body.reason || "Rejeitada na operação.";
    } else if (action === "reserve") {
      requirePermission(database, actor, "requests.process");
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
      requirePermission(database, actor, "requests.process");
      if (!["reserved", "partially_fulfilled"].includes(request.status)) throw new Error("Somente solicitações reservadas podem ser atendidas.");
      if (!body.items?.some((entry) => Number.isInteger(entry.quantity) && entry.quantity > 0)) throw new Error("Informe pelo menos uma quantidade positiva para atendimento.");
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
      if (request.requester !== actor.id) requirePermission(database, actor, "requests.cancel_any");
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

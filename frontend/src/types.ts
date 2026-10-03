export type Role = "admin" | "approver" | "operations" | "operator" | "requester" | "industry";

export type User = {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile: {
    id: string;
    role: Role;
    department: string;
    phone: string;
    industry: string | null;
  };
  is_active?: boolean;
};

export type LookupType = "categories" | "departments" | "industries" | "locations" | "suppliers";

export type LookupRecord = {
  id: string;
  name: string;
  is_active: boolean;
};

export type Category = {
  id: string;
  name: string;
  is_active: boolean;
};

export type Product = {
  id: string;
  sku: string;
  name: string;
  description: string;
  category: string | null;
  unit: string;
  minimum_stock: number;
  is_active: boolean;
};

export type StockBalance = {
  id: string;
  product: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  updated_at: string;
};

export type Industry = {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type IndustryBalance = {
  industry_id: string;
  industry_name: string;
  product_id: string;
  sku: string;
  product_name: string;
  quantity: number;
};

export type StockLocation = {
  id: string;
  name: string;
  kind: "cd" | "event" | "other";
  description: string;
  is_active: boolean;
};

export type StockPosition = {
  id: string;
  product: { id: string; sku: string; name: string };
  location: { id: string; name: string; kind: StockLocation["kind"] };
  quantity: number;
  updated_at: string;
};

export type StockTransfer = {
  id: string;
  product: string;
  industry_id: string;
  quantity: number;
  from_location_id: string;
  to_location_id: string;
  notes: string;
  created_by: string | null;
  created_at: string;
  movements: StockMovement[];
};

export type StockExitOrder = {
  id: string;
  product: string;
  industry: string | null;
  location: string | null;
  quantity: number;
  note: string;
  status: "pending" | "confirmed" | "cancelled";
  qr_token?: string;
  requested_by: string;
  confirmed_by: string | null;
  created_at: string;
  confirmed_at: string | null;
};

export type StockMovement = {
  id: string;
  product: string;
  industry: string | null;
  location: string | null;
  to_location: string | null;
  transfer: string | null;
  movement_type: "entry" | "exit" | "adjustment" | "transfer";
  quantity_delta: number;
  reference: string;
  note: string;
  created_at: string;
};

export type TradeRequestItem = {
  id: string;
  product: string;
  kind: "fisico" | "voucher" | "cartao" | "outro";
  qty_requested: number;
  qty_received: number;
  qty_delivered: number;
  unit_value: string;
  notes: string;
};

export type TradeRequestHistory = {
  id: string;
  from_status: string;
  to_status: string;
  actor: string | null;
  comment: string;
  created_at: string;
};

export type TradeDeliveryItem = {
  id: string;
  product: string;
  quantity: number;
  balance_after: number;
};

export type TradeDelivery = {
  id: string;
  code: string;
  received_by_name: string;
  received_by_document: string;
  received_by_email: string;
  received_by_phone: string;
  recipient: string;
  notes: string;
  delivered_by: string | null;
  created_at: string;
  signature_present: boolean;
  items: TradeDeliveryItem[];
};

export type TradeRequest = {
  id: string;
  public_code: string;
  industry_id: string;
  requester: string;
  department: string;
  purpose: string;
  recipient: string;
  action_type: "campanha" | "premiacao" | "evento" | "feirao" | "outro";
  delivery_place: string;
  notes: string;
  status: string;
  purchase_ticket_no: string;
  invoice_no: string;
  total_value: string;
  approved_by: string | null;
  approved_at: string | null;
  approval_notes: string;
  rejection_reason: string;
  received_at: string | null;
  submitted_at: string;
  created_at: string;
  updated_at: string;
  items: TradeRequestItem[];
  history: TradeRequestHistory[];
  deliveries: TradeDelivery[];
};

export type TradeRequestItemDraft = {
  product: string;
  kind: TradeRequestItem["kind"];
  qty_requested: number;
  unit_value: string;
  notes?: string;
};

export type GiftRequestItem = {
  id: string;
  product: string;
  quantity: number;
  reserved_quantity: number;
  fulfilled_quantity: number;
  remaining_quantity: number;
};

export type GiftRequest = {
  id: string;
  requester: string;
  status: string;
  justification: string;
  rejection_reason: string;
  approved_by: string | null;
  items: GiftRequestItem[];
  created_at: string;
};

export type AuditEvent = {
  id: string;
  actor: string | null;
  actor_email?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  metadata: Record<string, unknown>;
  request_id?: string;
  created_at: string;
};

export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

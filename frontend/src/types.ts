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
  };
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

export type StockMovement = {
  id: string;
  product: string;
  movement_type: "entry" | "exit" | "adjustment";
  quantity_delta: number;
  reference: string;
  note: string;
  created_at: string;
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


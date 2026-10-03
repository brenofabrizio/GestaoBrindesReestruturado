import type { Role, User } from "../types";

const permissions: Record<Role, string[]> = {
  admin: ["*"],
  approver: ["dashboard.view", "catalog.view", "catalog.manage", "stock.view", "stock.entry", "stock.exit", "stock.adjust", "stock.transfer", "requests.create", "requests.view_own", "requests.view_department", "requests.approve", "requests.cancel_any", "audit.view"],
  operations: ["dashboard.view", "catalog.view", "stock.view", "stock.entry", "stock.transfer", "stock.receive", "stock.exit_confirm", "audit.view"],
  operator: ["dashboard.view", "catalog.view", "stock.view", "stock.entry", "stock.transfer", "stock.receive", "stock.exit_confirm", "audit.view"],
  requester: ["dashboard.view", "catalog.view", "requests.create", "requests.view_own"],
  industry: ["dashboard.view", "catalog.view", "stock.view", "requests.create", "requests.view_own"],
};

export function can(user: User | null, permission: string) {
  if (!user) return false;
  const own = permissions[user.profile.role] || [];
  return own.includes("*") || own.includes(permission);
}

export function canViewStockMovementHistory(user: User | null) {
  return Boolean(user && user.profile.role !== "industry");
}

export function inventoryScopeForRole(role: string | null | undefined): "industry" | "global" {
  return role === "industry" ? "industry" : "global";
}

export function canAny(user: User | null, permissionsToCheck: string[]) {
  return permissionsToCheck.some((permission) => can(user, permission));
}

export function requestCapabilities(user: User | null) {
  return {
    canCreate: can(user, "requests.create"),
    canApprove: can(user, "requests.approve"),
    canProcess: can(user, "requests.process"),
    canCancelAny: can(user, "requests.cancel_any"),
    canViewRequests: canAny(user, ["requests.view_own", "requests.view_department", "requests.view_all", "requests.approve", "requests.process"]),
  };
}

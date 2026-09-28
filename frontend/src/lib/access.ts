import type { Role, User } from "../types";

const permissions: Record<Role, string[]> = {
  admin: ["*"],
  approver: ["catalog.view", "catalog.manage", "stock.view", "requests.create", "requests.view_all", "requests.approve", "requests.process", "audit.view"],
  operations: ["catalog.view", "catalog.manage", "stock.view", "requests.view_all", "requests.process", "audit.view"],
  operator: ["catalog.view", "stock.view", "requests.view_all", "requests.process", "audit.view"],
  requester: ["catalog.view", "requests.create", "requests.view_own"],
  industry: ["catalog.view", "stock.view", "requests.view_own"],
};

export function can(user: User | null, permission: string) {
  if (!user) return false;
  const own = permissions[user.profile.role] || [];
  return own.includes("*") || own.includes(permission);
}


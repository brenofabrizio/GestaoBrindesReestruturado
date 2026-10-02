import type { User } from "../types";
import { localDb } from "./localStore";

export function can(user: User | null, permission: string) {
  return localDb.hasPermission(user, permission);
}

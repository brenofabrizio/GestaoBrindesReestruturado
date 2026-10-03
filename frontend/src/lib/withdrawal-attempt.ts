type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">;

type WithdrawalPayload = {
  public_code: string;
  received_by_name: string;
  received_by_document?: string;
  received_by_email?: string;
  received_by_phone?: string;
  recipient?: string;
  signature_data: string;
  notes?: string;
  items: { item_id: string; qty: number }[];
};

type StoredAttempt = { idempotencyKey: string; fingerprint: string };

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, item]) => [key, canonicalize(item)]),
    );
  }
  return value;
}

function storageKey(requestId: string) {
  return `trade-withdrawal:${requestId}`;
}

async function fingerprint(payload: WithdrawalPayload): Promise<string> {
  const canonicalPayload = {
    ...payload,
    items: [...payload.items].sort((left, right) => left.item_id.localeCompare(right.item_id)),
  };
  const bytes = new TextEncoder().encode(JSON.stringify(canonicalize(canonicalPayload)));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function createWithdrawalAttempt(
  storage: StorageLike,
  requestId: string,
  payload: WithdrawalPayload,
  createKey: () => string = () => globalThis.crypto.randomUUID(),
): Promise<string> {
  const key = storageKey(requestId);
  const payloadFingerprint = await fingerprint(payload);
  const savedValue = storage.getItem(key);
  if (savedValue) {
    try {
      const saved = JSON.parse(savedValue) as StoredAttempt;
      if (saved.fingerprint === payloadFingerprint && typeof saved.idempotencyKey === "string") {
        return saved.idempotencyKey;
      }
    } catch {
      storage.removeItem(key);
    }
    throw new Error("Há uma tentativa de retirada sem confirmação. Atualize a solicitação antes de iniciar uma nova tentativa.");
  }
  const attempt: StoredAttempt = { idempotencyKey: createKey(), fingerprint: payloadFingerprint };
  storage.setItem(key, JSON.stringify(attempt));
  return attempt.idempotencyKey;
}

export function clearWithdrawalAttempt(storage: StorageLike, requestId: string) {
  storage.removeItem(storageKey(requestId));
}

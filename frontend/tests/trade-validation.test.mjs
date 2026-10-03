import { strict as assert } from "node:assert";
import { test } from "node:test";
import { validateTradeItemDraft } from "../src/lib/trade-validation.ts";
import { createWithdrawalAttempt, clearWithdrawalAttempt } from "../src/lib/withdrawal-attempt.ts";

function makeStorage() {
  const entries = new Map();
  return {
    getItem: (key) => entries.get(key) ?? null,
    setItem: (key, value) => entries.set(key, value),
    removeItem: (key) => entries.delete(key),
    entries,
  };
}

test("trade item validation rejects invalid quantities and currency precision", () => {
  assert.equal(validateTradeItemDraft(1, "12.50"), null);
  assert.equal(validateTradeItemDraft(0, "12.50"), "Informe uma quantidade inteira maior que zero.");
  assert.equal(validateTradeItemDraft(1.5, "12.50"), "Informe uma quantidade inteira maior que zero.");
  assert.equal(validateTradeItemDraft(1, "-1"), "Informe um valor unitário válido, não negativo e com até duas casas decimais.");
  assert.equal(validateTradeItemDraft(1, "1.234"), "Informe um valor unitário válido, não negativo e com até duas casas decimais.");
});

test("withdrawal attempt reuses key only for identical payload and stores no signature", async () => {
  const storage = makeStorage();
  const payload = { public_code: "TR-123456789ABC", received_by_name: "Pessoa", signature_data: "data:image/png;base64,private-signature", items: [{ item_id: "product-1", qty: 2 }] };
  let keyCount = 0;
  const createKey = () => `attempt-key-${++keyCount}`;
  const first = await createWithdrawalAttempt(storage, "request-1", payload, createKey);
  const retry = await createWithdrawalAttempt(storage, "request-1", payload, createKey);

  assert.equal(first, "attempt-key-1");
  assert.equal(retry, first);
  assert.equal(keyCount, 1);
  assert.equal([...storage.entries.values()].some((value) => value.includes("private-signature")), false);
  await assert.rejects(
    createWithdrawalAttempt(storage, "request-1", { ...payload, items: [{ item_id: "product-1", qty: 3 }] }, createKey),
    /Atualize a solicitação antes de iniciar uma nova tentativa/,
  );
  clearWithdrawalAttempt(storage, "request-1");
  assert.equal(await createWithdrawalAttempt(storage, "request-1", payload, createKey), "attempt-key-2");
});

import { strict as assert } from "node:assert";
import { hasScannedQrToken } from "../src/lib/exit-orders.ts";
import { test } from "node:test";

test("QR submission requires a non-empty scanned value", () => {
  assert.equal(hasScannedQrToken(""), false);
  assert.equal(hasScannedQrToken("  \n"), false);
  assert.equal(hasScannedQrToken("  qr-123\n"), true);
});

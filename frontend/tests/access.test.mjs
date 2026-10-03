import { strict as assert } from "node:assert";
import { test } from "node:test";
import { can, requestCapabilities, canViewStockMovementHistory } from "../src/lib/access.ts";

test("operational profile cannot see approval actions without requests.approve", () => {
  const user = { profile: { role: "operator" } };
  assert.deepEqual(requestCapabilities(user), {
    canCreate: false,
    canApprove: false,
    canProcess: false,
    canCancelAny: false,
    canViewRequests: false,
  });
});

test("approver sees approval actions and requester only sees own create action", () => {
  assert.deepEqual(requestCapabilities({ profile: { role: "approver" } }), {
    canCreate: true,
    canApprove: true,
    canProcess: false,
    canCancelAny: true,
    canViewRequests: true,
  });
  assert.deepEqual(requestCapabilities({ profile: { role: "requester" } }), {
    canCreate: true,
    canApprove: false,
    canProcess: false,
    canCancelAny: false,
    canViewRequests: true,
  });
});

test("industry profiles cannot read global movement ledger", () => {
  assert.equal(canViewStockMovementHistory({ profile: { role: "industry" } }), false);
  assert.equal(canViewStockMovementHistory({ profile: { role: "operator" } }), true);
});

test("industry profile can create TRADE but remains scoped to its own request view", () => {
  const user = { profile: { role: "industry" } };
  assert.equal(can(user, "requests.create"), true);
  assert.equal(requestCapabilities(user).canViewRequests, true);
});

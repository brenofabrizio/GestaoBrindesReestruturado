import { strict as assert } from "node:assert";
import { test } from "node:test";
import { inventoryScopeForRole } from "../src/lib/access.ts";

test("industry profile uses industry aggregate instead of global physical stock", () => {
  assert.equal(inventoryScopeForRole("industry"), "industry");
  assert.equal(inventoryScopeForRole("operator"), "global");
  assert.equal(inventoryScopeForRole("admin"), "global");
});

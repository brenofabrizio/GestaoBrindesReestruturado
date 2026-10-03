import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const seed = JSON.parse(readFileSync(new URL("../src/data/seed.json", import.meta.url), "utf8"));
const loginSource = readFileSync(new URL("../src/pages/LoginPage.tsx", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");

test("demo seed does not store plaintext user passwords", () => {
  assert.ok(seed.users.length > 0);
  for (const user of seed.users) assert.equal(Object.hasOwn(user, "password"), false);
});

test("login UI and frontend guide do not publish demo credentials", () => {
  assert.doesNotMatch(loginSource, /demo-box|temporário de demonstração/i);
  assert.doesNotMatch(readme, /senha\s*\|/i);
});

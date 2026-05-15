/**
 * @quarry/sdk — TypeScript client for Quarry
 *
 * Auto-generated types from docs/openapi.yaml; hand-written client wrapper.
 *
 * @example
 * ```ts
 * import { QuarryClient } from "@quarry/sdk";
 *
 * const client = new QuarryClient({
 *   baseUrl: "https://your-quarry.example.com",
 *   token: process.env.QUARRY_API_TOKEN,
 * });
 *
 * const alerts = await client.alerts.list({ severity: "critical" });
 * ```
 */

export { QuarryClient } from "./client.js";
export type { QuarryClientOptions } from "./client.js";
export * from "./types.js";

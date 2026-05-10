/**
 * AiSOC Osquery Pack Types
 *
 * TypeScript types mirroring the Python Pydantic models in
 * services/api/app/services/pack_loader.py and the YAML schema
 * documented in packs/README.md.
 *
 * AiSOC — open-source AI Security Operations Center platform
 * MIT License
 */

// ---------------------------------------------------------------------------
// Pack query
// ---------------------------------------------------------------------------

/** MITRE ATT&CK technique reference attached to a pack query. */
export interface PackQueryMitre {
  /** ATT&CK technique ID, e.g. "T1098" */
  technique_id: string;
  /** Human-readable technique name */
  technique_name: string;
}

/** A single osquery query within a pack. */
export interface PackQuery {
  /** SQL statement executed by osquery */
  sql: string;
  /** Polling interval in seconds */
  interval: number;
  /** AiSOC severity tier: info | low | medium | high */
  severity: "info" | "low" | "medium" | "high";
  /** Optional snapshot mode flag */
  snapshot?: boolean;
  /** Optional list of MITRE ATT&CK technique references */
  mitre?: PackQueryMitre[];
  /** Optional external reference URLs */
  references?: string[];
  /** Optional description of the query */
  description?: string;
}

// ---------------------------------------------------------------------------
// Pack
// ---------------------------------------------------------------------------

/** Target platforms for a pack. */
export type PackPlatform = "linux" | "darwin" | "windows" | "all";

/**
 * An AiSOC osquery pack as returned by the API.
 *
 * Maps 1-to-1 with the Python OsqueryPack Pydantic model in
 * services/api/app/services/pack_loader.py.
 */
export interface OsqueryPack {
  /** Unique pack identifier, e.g. "aisoc-fim-baseline" */
  id: string;
  /** Display name */
  name: string;
  /** Semantic version string */
  version: string;
  /** List of target platforms */
  platforms: PackPlatform[];
  /** Human-readable description */
  description: string;
  /** Optional osquery SQL discovery queries (run before the pack is activated) */
  discovery?: string[];
  /** Named queries within the pack */
  queries: Record<string, PackQuery>;
  /**
   * FIM file path patterns keyed by category name.
   * Corresponds to the osquery file_paths config block.
   */
  file_paths?: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// API response shapes
// ---------------------------------------------------------------------------

/** List item returned by GET /v1/packs (catalog listing). */
export interface PackSummary {
  id: string;
  name: string;
  version: string;
  platforms: PackPlatform[];
  description: string;
  query_count: number;
  is_fim_pack: boolean;
}

/** Full pack detail returned by GET /v1/packs/{pack_id}. */
export interface PackDetail extends OsqueryPack {
  /** Rendered format variants for easy consumption by fleet managers */
  render?: {
    /** osctrl JSON pack format */
    osctrl?: Record<string, unknown>;
    /** FleetDM pack format */
    fleetdm?: Record<string, unknown>;
    /** Canonical osquery JSON config fragment */
    osquery_json?: Record<string, unknown>;
  };
}

/** Item in the tenant's assigned pack list. */
export interface AssignedPack {
  pack_id: string;
  assigned_at: string; // ISO-8601
}

/** Response from GET /v1/packs/assigned */
export interface AssignedPacksResponse {
  packs: AssignedPack[];
}

/** Request body for POST /v1/packs/assign */
export interface AssignPackRequest {
  pack_id: string;
}

/** Compiled osquery configuration returned by GET /v1/packs/config */
export interface CompiledOsqueryConfig {
  /** Named osquery packs block */
  packs: Record<string, { queries: Record<string, PackQuery> }>;
  /** Merged file_paths block across all assigned packs */
  file_paths?: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// FIM types
// ---------------------------------------------------------------------------

/** A file integrity monitoring event as stored by osquery file_events. */
export interface FimEvent {
  /** Target file path */
  target_path: string;
  /** Action performed: CREATED | MODIFIED | DELETED | MOVED_FROM | MOVED_TO */
  action: "CREATED" | "MODIFIED" | "DELETED" | "MOVED_FROM" | "MOVED_TO";
  /** MD5 hash of the file (empty for DELETED events) */
  md5?: string;
  /** SHA-256 hash of the file (empty for DELETED events) */
  sha256?: string;
  /** Username associated with the event */
  username?: string;
  /** Unix timestamp */
  time: number;
  /** Host identifier */
  host_identifier: string;
}

/** Summary statistics shown in the FIM dashboard widget. */
export interface FimSummary {
  /** Total events in the selected time range */
  total_events: number;
  /** Breakdown by action type */
  by_action: Record<string, number>;
  /** Top modified paths */
  top_paths: Array<{ path: string; count: number }>;
  /** Number of distinct hosts with FIM activity */
  affected_hosts: number;
}

import type { TablerIcon } from "@tabler/icons-react";
import type { InputMeasurements, JDBoundary, JDFarm, JDField, JDFieldOp, JDOrg, JDProductDetails, OutputMeasurements } from "./jd";

// -----------------------------------------------------------------------------
// Core Models
// -----------------------------------------------------------------------------

export interface Paginated<T> {
  data: T[];
  count: number;
}

export interface FieldOpChildPreview {
  new_op_children: SyncLink<"boundary" | "op_input" | "op_output">[];
  new_org_children: SyncLink<"product">[];
}

// -----------------------------------------------------------------------------
// User Models
// -----------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_superuser: boolean;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

// -----------------------------------------------------------------------------
// Sync Tree Models
// -----------------------------------------------------------------------------

export interface TableMap {
  org: JDOrg;
  farm: JDFarm;
  field: JDField;
  boundary: JDBoundary;
  field_op: JDFieldOp;
  product: JDProductDetails;
  op_input: InputMeasurements;
  op_output: OutputMeasurements;
}

export type SyncStatus =
  | "Synced"
  | "Pending"
  | "Paused"
  | "Unsynced"
  | "Inaccessible"
  | "Conflict";

export interface SyncStatusDetails {
  color: string;
  icon: TablerIcon;
  description: string;
  transitions: Partial<Record<SyncStatus, string>>;
  active: boolean;
}

interface BaseSyncLink<K extends keyof TableMap> {
  id: string;
  uri: string;
  data: TableMap[K];
  status: SyncStatus;
  local_persistent: boolean;
  table_name: K;
  table_key: Record<string, string> | null;
  children: AnySyncLink[];
}

export type SyncLink<K extends keyof TableMap = keyof TableMap> =
  K extends keyof TableMap ? BaseSyncLink<K> : never;

export type AnySyncLink = {[K in keyof TableMap]: SyncLink<K>}[keyof TableMap];

export interface SyncUpdate {
  status: SyncStatus;
}

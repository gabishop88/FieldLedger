// -----------------------------------------------------------------------------
// Core Models
// -----------------------------------------------------------------------------

import type { TablerIcon } from "@tabler/icons-react";
import type { JDLinkedData } from "./jd";

export interface Paginated<T> {
    data: T[];
    count: number;
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

export type SyncableTable =
    | "org"
    | "farm"
    | "field"
    | "boundary"
    | "field_op"

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

// TODO: rename SyncLink
export interface SyncLink<T extends JDLinkedData = JDLinkedData> {
    id: string;
    uri: string;
    data: T;
    status: SyncStatus;
    local_persistent: boolean;
    table_name: SyncableTable;
    table_key: Record<string, string> | null;
    children: SyncLink[];
}

export interface SyncUpdate {
    status: SyncStatus;
}

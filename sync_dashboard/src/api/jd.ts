import {
    IconAlertTriangleFilled,
    IconCircleCheckFilled,
    IconCircleDashedCheck,
    IconLockFilled,
    IconPlayerPauseFilled
} from "@tabler/icons-react";

import client from "./client";

export interface JDAuthInfo {
    authorized: boolean;
    auth_uri: string;
}

export const statusDetails = {
    Synced: {
        color: "green",
        icon: IconCircleCheckFilled,
        description: "Resource linked; up to date.",
        transitions: {
            Paused: "Keep Link, stop recieving updates from John Deere.",
            Unsynced: "Remove children and linked data. If data is needed outside of sync, status will be set to 'Paused' but will still try to remove children.",
        },
        active: true,
    },
    Pending: {
        color: "yellow",
        icon: IconCircleCheckFilled,
        description: "Resource linked; not up to date.",
        transitions: {
            Synced: "In case it has been pending for too long, attempt to resync manually.",
            Unsynced: "In case it has been pending for too long, give up and unsync.",
        },
        active: true,
    },
    Paused: {
        color: "orange",
        icon: IconPlayerPauseFilled,
        description: "Resource linked; updates paused.",
        transitions: {
            Synced: "Keep link and resume updates from John Deere.",
            Unsynced: "Attempt to remove link and unsync children.",
        },
        active: true,
    },
    Unsynced: {
        color: "gray",
        icon: IconCircleDashedCheck,
        description: "Resource discovered; not linked.",
        transitions: {
            Synced: "Start Sync Process. Look for matching records or create one.",
        },
        active: false,
    },
    Inaccessible: {
        color: "red",
        icon: IconAlertTriangleFilled,
        description: "Organization discovered; access not enabled.",
        transitions: {
            Unsynced: "If you have enabled access to this org, click to try to clear error status.",
        },
        active: false,
    },
    Conflict: {
        color: "dark",
        icon: IconLockFilled,
        description: "Organization discovered; linked by another user.",
        transitions: {
            Unsynced: "Attempt to sync, only works if there are no other users syncing this org.",
        },
        active: false,
    },
}

export type SyncStatus = keyof typeof statusDetails;

export interface SyncTreeNode {
    id: string;
    uri: string;
    data: Record<string, unknown>;
    status: SyncStatus;
    local_persistent: boolean;
    table_name: string;
    table_key: Record<string, unknown> | null;
    children: SyncTreeNode[];
}

interface SyncUpdate {
    status: SyncStatus;
}

interface Paginated<T> {
    data: T[];
    count: number;
}

export async function getJDAuth(): Promise<JDAuthInfo> {
    try {
        const { data } = await client.get<JDAuthInfo>("/jd/authorization-link");
        return data;
    } catch {
        return { authorized: false, auth_uri: "" }
    }
}

export async function deleteJDAuth(): Promise<void> {
    await client.delete("/jd/authorization-link");
}

export async function getSyncTrees(): Promise<SyncTreeNode[]> {
    try {
        const { data } = await client.get<Paginated<SyncTreeNode>>("/jd/sync-trees");
        return data.data;
    } catch {
        return []
    }
}

export async function updateSyncStatus(uri: string, status: SyncStatus): Promise<void> {
    await client.patch(`jd/resource/${uri}`, { status } satisfies SyncUpdate);
}

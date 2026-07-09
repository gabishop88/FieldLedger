import type { Paginated, SyncLink, SyncStatus, SyncUpdate } from "../types/fl";
import type { JDAuthInfo, JDOrg } from "../types/jd";
import client from "./client";

export async function jdAuthLinkRequest(): Promise<JDAuthInfo> {
    try {
        const { data } = await client.get<JDAuthInfo>("/jd/authorization-link");
        return data;
    } catch {
        return { authorized: false, auth_uri: "" }
    }
}

export async function jdDeleteSyncRequest(): Promise<void> {
    await client.delete("/jd/authorization-link");
}

export async function jdSyncTreesRequest(): Promise<SyncLink<JDOrg>[]> {
    try {
        const { data } = await client.get<Paginated<SyncLink<JDOrg>>>("/jd/sync-trees");
        return data.data;
    } catch {
        return []
    }
}

export async function jdUpdateSyncStatusRequest(uri: string, status: SyncStatus): Promise<void> {
    await client.patch(`jd/resource/${uri}`, { status } satisfies SyncUpdate);
}

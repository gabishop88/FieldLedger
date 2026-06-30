import client from "./client";

export interface JDAuthInfo {
    authorized: boolean;
    auth_uri: string;
}

export interface SyncTreeNode {
    id: string;
    uri: string;
    data: Record<string, unknown>;
    status: string;
    local_persistent: boolean;
    table_name: string;
    table_key: Record<string, unknown> | null;
    children: SyncTreeNode[];
}

interface Paginated<T> {
    data: T[];
    count: number;
}

export async function getJDAuth(): Promise<JDAuthInfo> {
    const { data } = await client.get<JDAuthInfo>("/jd/authorization-link");
    return data;
}

export async function getSyncTrees(): Promise<SyncTreeNode[]> {
    const { data } = await client.get<Paginated<SyncTreeNode>>("/jd/sync-trees");
    return data.data;
}

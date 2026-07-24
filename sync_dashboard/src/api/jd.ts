import type { FieldOpChildPreview, Paginated, SyncLink, SyncStatus, SyncUpdate } from "../types/fl";
import type { JDAuthInfo } from "../types/jd";
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

export async function jdSyncTreesRequest(): Promise<SyncLink<"org">[]> {
  try {
    const { data } = await client.get<Paginated<SyncLink<"org">>>("/jd/sync-trees");
    return data.data;
  } catch {
    return []
  }
}

export async function jdUpdateSyncStatusRequest(uri: string, status: SyncStatus): Promise<void> {
  await client.patch(`jd/resource/${uri}`, { status } satisfies SyncUpdate);
}

export async function jdPrepareOpRequest(uri: string): Promise<FieldOpChildPreview> {
  try {
    const { data } = await client.get(`jd/resource/prepare-operation/${uri}`);
    return data;
  } catch {
    return {"new_org_children": [], "new_op_children": []}
  }
}
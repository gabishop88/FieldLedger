import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jdSyncTreesRequest, jdUpdateSyncStatusRequest } from "../api/jd";
import type { SyncStatus } from "../types/fl";

export function useSyncTree(enabled: boolean) {
    return useQuery({
        queryKey: ["jd", "syncTree"],
        queryFn: jdSyncTreesRequest,
        enabled,
        staleTime: Infinity,
        refetchOnWindowFocus: false,
        refetchOnMount: false,
        refetchOnReconnect: false,
    });
}

let refreshTimeout: ReturnType<typeof setTimeout> | undefined;

export function useUpdateSync() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (
            { uri, newStatus }: { uri: string, newStatus: SyncStatus }
        ) => jdUpdateSyncStatusRequest(uri, newStatus),

        onSuccess: () => {
            clearTimeout(refreshTimeout);
            refreshTimeout = setTimeout(() => queryClient.invalidateQueries(
                { queryKey: ["jd", "syncTree"] }
            ), 1000);
        }
    });
}

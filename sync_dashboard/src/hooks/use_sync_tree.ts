import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getSyncTrees, updateSyncStatus, type SyncStatus } from "../api/jd";

export function useSyncTree(enabled: boolean) {
    return useQuery({
        queryKey: ["jd", "syncTree"],
        queryFn: getSyncTrees,
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
        ) => updateSyncStatus(uri, newStatus),

        onSuccess: () => {
            clearTimeout(refreshTimeout);
            refreshTimeout = setTimeout(() => queryClient.invalidateQueries(
                { queryKey: ["jd", "syncTree"] }
            ), 1000);
        }
    });
}

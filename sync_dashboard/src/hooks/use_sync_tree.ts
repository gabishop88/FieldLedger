import { useQuery } from "@tanstack/react-query";
import { getSyncTrees } from "../api/jd";

export function useSyncTree(enabled: boolean) {
    return useQuery({
        queryKey: ["jd", "syncTree"],
        queryFn: getSyncTrees,
        enabled,
    });
}

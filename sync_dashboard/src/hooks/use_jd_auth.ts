import { useQuery } from "@tanstack/react-query";
import { getJDAuth } from "../api/jd";

export function useJDAuth(enabled: boolean) {
    return useQuery({
        queryKey: ["jd", "auth"],
        queryFn: getJDAuth,
        enabled,
    });
}

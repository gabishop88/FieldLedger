import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteJDAuth, getJDAuth } from "../api/jd";

export function useJDAuth(enabled: boolean) {
    return useQuery({
        queryKey: ["jd", "auth"],
        queryFn: getJDAuth,
        enabled,
    });
}

export function useDeleteJDAuth() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: deleteJDAuth,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jd"] }),
    })
}

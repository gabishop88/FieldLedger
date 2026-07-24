import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jdDeleteSyncRequest, jdAuthLinkRequest } from "../api/jd";

export function useJDAuth(enabled: boolean) {
  return useQuery({
    queryKey: ["jd", "auth"],
    queryFn: jdAuthLinkRequest,
    enabled,
  });
}

export function useDeleteJDAuth() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: jdDeleteSyncRequest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jd"] }),
  })
}

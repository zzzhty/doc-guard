import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getChange, listChanges, scanCommit, scanRecent } from "../api/changes";

export function useChanges(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "changes"],
    queryFn: () => listChanges(projectId),
    enabled: !!projectId,
  });
}

export function useChange(projectId: number, commitId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "changes", commitId],
    queryFn: () => getChange(projectId, commitId),
    enabled: !!projectId && !!commitId,
  });
}

export function useScanCommit(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (commitHash: string) => scanCommit(projectId, commitHash),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "changes"] }),
  });
}

export function useScanRecent(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (count: number) => scanRecent(projectId, count),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "changes"] }),
  });
}

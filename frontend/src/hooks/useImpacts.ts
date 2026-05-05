import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analyzeCommit, listImpacts, updateImpactStatus } from "../api/impacts";

export function useImpacts(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "impacts"],
    queryFn: () => listImpacts(projectId),
    enabled: !!projectId,
  });
}

export function useAnalyzeCommit(projectId: number, commitId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => analyzeCommit(projectId, commitId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "impacts"] });
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "changes", commitId] });
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "changes"] });
    },
  });
}

export function useUpdateImpactStatus(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ impactId, status }: { impactId: number; status: string }) =>
      updateImpactStatus(projectId, impactId, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects", projectId, "impacts"] }),
  });
}

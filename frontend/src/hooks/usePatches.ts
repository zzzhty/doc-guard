import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { approvePatch, generatePatch, getPatch, rejectPatch, updatePatch } from "../api/patches";

export function usePatch(patchId: number) {
  return useQuery({
    queryKey: ["patches", patchId],
    queryFn: () => getPatch(patchId),
    enabled: !!patchId,
  });
}

export function useGeneratePatch(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ impactId, changeType }: { impactId: number; changeType?: string }) =>
      generatePatch(projectId, impactId, changeType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "impacts"] });
    },
  });
}

export function useUpdatePatch(patchId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patchedContent: string) => updatePatch(patchId, patchedContent),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["patches", patchId] }),
  });
}

export function useApprovePatch(patchId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => approvePatch(patchId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["patches", patchId] }),
  });
}

export function useRejectPatch(patchId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => rejectPatch(patchId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["patches", patchId] }),
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { closeDocPR, createDocPR, getDocPR, listDocPRs, refreshDocPR } from "../api/docPrs";

export function useDocPRs(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "doc-prs"],
    queryFn: () => listDocPRs(projectId),
    enabled: !!projectId,
  });
}

export function useDocPR(docPrId: number) {
  return useQuery({
    queryKey: ["doc-prs", docPrId],
    queryFn: () => getDocPR(docPrId),
    enabled: !!docPrId,
  });
}

export function useCreateDocPR(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patchIds: number[]) => createDocPR(projectId, patchIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "doc-prs"] });
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "impacts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", projectId] });
    },
  });
}

export function useRefreshDocPR(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (docPrId: number) => refreshDocPR(docPrId),
    onSuccess: (docPr) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "doc-prs"] });
      queryClient.invalidateQueries({ queryKey: ["doc-prs", docPr.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", projectId] });
    },
  });
}

export function useCloseDocPR(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (docPrId: number) => closeDocPR(docPrId),
    onSuccess: (docPr) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "doc-prs"] });
      queryClient.invalidateQueries({ queryKey: ["doc-prs", docPr.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", projectId] });
    },
  });
}

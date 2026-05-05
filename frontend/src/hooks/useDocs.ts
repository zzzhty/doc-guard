import { useQuery } from "@tanstack/react-query";
import { getDocContent, getDocTree } from "../api/docs";

export function useDocTree(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "docs", "tree"],
    queryFn: () => getDocTree(projectId),
    enabled: !!projectId,
  });
}

export function useDocContent(projectId: number, path: string | null) {
  return useQuery({
    queryKey: ["projects", projectId, "docs", "content", path],
    queryFn: () => getDocContent(projectId, path || ""),
    enabled: !!projectId && !!path,
  });
}

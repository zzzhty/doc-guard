import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../api/dashboard";

export function useDashboard(projectId: number | null) {
  return useQuery({
    queryKey: ["dashboard", projectId],
    queryFn: () => getDashboard(projectId as number),
    enabled: !!projectId,
  });
}

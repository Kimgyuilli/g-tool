import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { CategoryCountsResponse } from "@/features/mail/types";

interface UseCategoryCountsProps {
  sourceFilter: "all" | "gmail" | "naver";
}

export function useCategoryCounts({
  sourceFilter,
}: UseCategoryCountsProps) {
  const [categoryCounts, setCategoryCounts] = useState<CategoryCountsResponse | null>(null);

  // Auto-load on deps change
  useEffect(() => {
    const sourceParam = sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
    apiFetch<CategoryCountsResponse>(
      `/api/inbox/category-counts?${sourceParam}`
    )
      .then(setCategoryCounts)
      .catch(() => setCategoryCounts(null));
  }, [sourceFilter]);

  const loadCategoryCounts = useCallback(async () => {
    try {
      const sourceParam = sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
      const data = await apiFetch<CategoryCountsResponse>(
        `/api/inbox/category-counts?${sourceParam}`
      );
      setCategoryCounts(data);
    } catch {
      setCategoryCounts(null);
    }
  }, [sourceFilter]);

  return { categoryCounts, loadCategoryCounts };
}

import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { CategoryCountsResponse } from "@/features/mail/types";

interface UseCategoryCountsProps {
  userId: number | null;
  sourceFilter: "all" | "gmail" | "naver";
}

export function useCategoryCounts({
  userId,
  sourceFilter,
}: UseCategoryCountsProps) {
  const [categoryCounts, setCategoryCounts] = useState<CategoryCountsResponse | null>(null);

  // Auto-load on deps change
  useEffect(() => {
    if (!userId) return;
    const sourceParam = sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
    apiFetch<CategoryCountsResponse>(
      `/api/inbox/category-counts?user_id=${userId}${sourceParam}`
    )
      .then(setCategoryCounts)
      .catch(() => setCategoryCounts(null));
  }, [userId, sourceFilter]);

  const loadCategoryCounts = useCallback(async () => {
    if (!userId) return;
    try {
      const sourceParam = sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
      const data = await apiFetch<CategoryCountsResponse>(
        `/api/inbox/category-counts?user_id=${userId}${sourceParam}`
      );
      setCategoryCounts(data);
    } catch {
      setCategoryCounts(null);
    }
  }, [userId, sourceFilter]);

  return { categoryCounts, loadCategoryCounts };
}

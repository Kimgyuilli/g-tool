import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { FeedbackStats } from "@/features/mail/types";

interface UseFeedbackStatsProps {
  userId: number | null;
}

export function useFeedbackStats({ userId }: UseFeedbackStatsProps) {
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);

  // Auto-load on deps change
  useEffect(() => {
    if (!userId) return;
    apiFetch<FeedbackStats>(
      `/api/classify/feedback-stats?user_id=${userId}`
    )
      .then(setFeedbackStats)
      .catch(() => setFeedbackStats(null));
  }, [userId]);

  const loadFeedbackStats = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await apiFetch<FeedbackStats>(
        `/api/classify/feedback-stats?user_id=${userId}`
      );
      setFeedbackStats(data);
    } catch {
      setFeedbackStats(null);
    }
  }, [userId]);

  return { feedbackStats, loadFeedbackStats };
}

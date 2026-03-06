import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { FeedbackStats } from "@/features/mail/types";

export function useFeedbackStats() {
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);

  // Auto-load
  useEffect(() => {
    apiFetch<FeedbackStats>("/api/classify/feedback-stats")
      .then(setFeedbackStats)
      .catch(() => setFeedbackStats(null));
  }, []);

  const loadFeedbackStats = useCallback(async () => {
    try {
      const data = await apiFetch<FeedbackStats>(
        "/api/classify/feedback-stats"
      );
      setFeedbackStats(data);
    } catch {
      setFeedbackStats(null);
    }
  }, []);

  return { feedbackStats, loadFeedbackStats };
}

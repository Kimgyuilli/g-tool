import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { MailMessage, MailListResponse } from "@/features/mail/types";

interface UseMessagesProps {
  sourceFilter: "all" | "gmail" | "naver";
  categoryFilter: string | null;
  limit: number;
}

export function useMessages({
  sourceFilter,
  categoryFilter,
  limit,
}: UseMessagesProps) {
  const [messages, setMessages] = useState<MailMessage[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadMessages = useCallback(
    async (newOffset?: number) => {
      const o = newOffset ?? offset;
      setLoading(true);
      try {
        const sourceParam = sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
        const categoryParam = categoryFilter ? `&category=${categoryFilter}` : "";
        const data = await apiFetch<MailListResponse>(
          `/api/inbox/messages?offset=${o}&limit=${limit}${sourceParam}${categoryParam}`
        );
        setMessages(data.messages);
        setTotal(data.total);
      } catch {
        setMessages([]);
      } finally {
        setLoading(false);
      }
    },
    [offset, sourceFilter, categoryFilter, limit]
  );

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  return {
    messages,
    setMessages,
    total,
    setTotal,
    offset,
    setOffset,
    loading,
    loadMessages,
  };
}

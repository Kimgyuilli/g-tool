import { useState, useCallback } from "react";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";
import type { MailMessage, MailListResponse } from "@/features/mail/types";

interface UseDragAndDropProps {
  sourceFilter: "all" | "gmail" | "naver";
  categoryFilter: string | null;
  offset: number;
  limit: number;
  handleUpdateCategory: (
    classificationId: number,
    newCategory: string,
    mailId: number
  ) => Promise<void>;
  setMessages: React.Dispatch<React.SetStateAction<MailMessage[]>>;
  setTotal: React.Dispatch<React.SetStateAction<number>>;
  loadMessages: (newOffset?: number) => Promise<void>;
  loadCategoryCounts: () => Promise<void>;
}

export function useDragAndDrop({
  sourceFilter,
  categoryFilter,
  offset,
  limit,
  handleUpdateCategory,
  setMessages,
  setTotal,
  loadMessages,
  loadCategoryCounts,
}: UseDragAndDropProps) {
  const [dragOverCategory, setDragOverCategory] = useState<string | null>(null);

  const handleDrop = useCallback(
    async (e: React.DragEvent, targetCategory: string) => {
      e.preventDefault();
      setDragOverCategory(null);

      const mailId = Number(e.dataTransfer.getData("mailId"));
      const classificationId = e.dataTransfer.getData("classificationId");

      if (!mailId) return;

      try {
        if (classificationId) {
          await handleUpdateCategory(Number(classificationId), targetCategory, mailId);
        } else {
          await apiFetch(`/api/classify/mails?mail_ids=${mailId}`, {
            method: "POST",
          });
          const sourceParam = sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
          const categoryParam = categoryFilter ? `&category=${categoryFilter}` : "";
          const data = await apiFetch<MailListResponse>(
            `/api/inbox/messages?offset=${offset}&limit=${limit}${sourceParam}${categoryParam}`
          );
          const updatedMail = data.messages.find((m) => m.id === mailId);
          if (updatedMail?.classification) {
            await handleUpdateCategory(
              updatedMail.classification.classification_id,
              targetCategory,
              mailId
            );
          }
          setMessages(data.messages);
          setTotal(data.total);
        }
        await loadCategoryCounts();
      } catch (err) {
        toast.error(`분류 실패: ${err}`);
        await loadMessages();
        await loadCategoryCounts();
      }
    },
    [
      sourceFilter,
      categoryFilter,
      offset,
      limit,
      handleUpdateCategory,
      setMessages,
      setTotal,
      loadMessages,
      loadCategoryCounts,
    ]
  );

  return { dragOverCategory, setDragOverCategory, handleDrop };
}

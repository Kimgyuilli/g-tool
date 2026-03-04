import { useState, useCallback } from "react";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";
import type { MailMessage, MailDetail } from "@/features/mail/types";
import type { UserInfo } from "@/features/auth/types";

interface UseMailActionsProps {
  userId: number | null;
  userInfo: UserInfo | null;
  sourceFilter: "all" | "gmail" | "naver";
  messages: MailMessage[];
  setMessages: React.Dispatch<React.SetStateAction<MailMessage[]>>;
  loadMessages: (newOffset?: number) => Promise<void>;
  loadCategoryCounts: () => Promise<void>;
  loadFeedbackStats: () => Promise<void>;
}

export function useMailActions({
  userId,
  userInfo,
  sourceFilter,
  messages,
  setMessages,
  loadMessages,
  loadCategoryCounts,
  loadFeedbackStats,
}: UseMailActionsProps) {
  const [syncing, setSyncing] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [applyingLabels, setApplyingLabels] = useState(false);
  const [selectedMail, setSelectedMail] = useState<MailDetail | null>(null);
  const [editingMailId, setEditingMailId] = useState<number | null>(null);

  const handleSync = useCallback(async () => {
    if (!userId || !userInfo) return;
    setSyncing(true);
    try {
      const promises = [];
      if (userInfo.google_connected) {
        promises.push(
          apiFetch<{ synced: number }>(
            `/api/gmail/sync?user_id=${userId}&max_results=50`,
            { method: "POST" }
          )
        );
      }
      if (userInfo.naver_connected) {
        promises.push(
          apiFetch<{ synced: number }>(
            `/api/naver/sync?user_id=${userId}&max_results=50`,
            { method: "POST" }
          )
        );
      }
      const results = await Promise.all(promises);
      const totalSynced = results.reduce((sum, r) => sum + r.synced, 0);
      toast.success(`${totalSynced}개의 새 메일을 동기화했습니다.`);
      await loadMessages(0);
      await loadCategoryCounts();
    } catch (err) {
      toast.error(`동기화 실패: ${err}`);
    } finally {
      setSyncing(false);
    }
  }, [userId, userInfo, loadMessages, loadCategoryCounts]);

  const handleClassify = useCallback(async () => {
    if (!userId) return;
    setClassifying(true);
    try {
      const sourceParam = sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
      const result = await apiFetch<{
        classified: number;
        results: { mail_id: number; category: string }[];
      }>(`/api/classify/mails?user_id=${userId}${sourceParam}`, { method: "POST" });
      toast.success(`${result.classified}개의 메일이 분류되었습니다.`);
      await loadMessages();
      await loadCategoryCounts();
    } catch (err) {
      toast.error(`분류 실패: ${err}`);
    } finally {
      setClassifying(false);
    }
  }, [userId, sourceFilter, loadMessages, loadCategoryCounts]);

  const handleApplyLabels = useCallback(async () => {
    if (!userId) return;
    const classifiedMails = messages.filter((m) => m.classification);
    if (classifiedMails.length === 0) {
      toast.warning("분류된 메일이 없습니다. 먼저 AI 분류를 실행하세요.");
      return;
    }
    setApplyingLabels(true);
    try {
      const result = await apiFetch<{ applied: number }>(
        `/api/gmail/apply-labels?user_id=${userId}`,
        {
          method: "POST",
          body: JSON.stringify({
            mail_ids: classifiedMails.map((m) => m.id),
          }),
        }
      );
      toast.success(`${result.applied}개의 Gmail 라벨이 적용되었습니다.`);
    } catch (err) {
      toast.error(`라벨 적용 실패: ${err}`);
    } finally {
      setApplyingLabels(false);
    }
  }, [userId, messages]);

  const handleUpdateCategory = useCallback(
    async (classificationId: number, newCategory: string, mailId: number) => {
      if (!userId) return;
      try {
        await apiFetch(`/api/classify/update?user_id=${userId}`, {
          method: "PUT",
          body: JSON.stringify({
            classification_id: classificationId,
            new_category: newCategory,
          }),
        });
        setMessages((prev) =>
          prev.map((m) =>
            m.id === mailId
              ? {
                  ...m,
                  classification: m.classification
                    ? {
                        ...m.classification,
                        category: newCategory,
                        user_feedback: newCategory,
                      }
                    : null,
                }
              : m
          )
        );
        if (selectedMail && selectedMail.id === mailId) {
          setSelectedMail((prev) =>
            prev
              ? {
                  ...prev,
                  classification: prev.classification
                    ? {
                        ...prev.classification,
                        category: newCategory,
                        user_feedback: newCategory,
                      }
                    : null,
                }
              : null
          );
        }
        setEditingMailId(null);
        await loadCategoryCounts();
        await loadFeedbackStats();
      } catch (err) {
        toast.error(`수정 실패: ${err}`);
      }
    },
    [userId, selectedMail, setMessages, loadCategoryCounts, loadFeedbackStats]
  );

  const handleSelectMail = useCallback(
    async (mail: MailMessage) => {
      if (!userId) return;
      try {
        const endpoint =
          mail.source === "gmail"
            ? `/api/gmail/messages/${mail.id}?user_id=${userId}`
            : `/api/naver/messages/${mail.id}?user_id=${userId}`;
        const detail = await apiFetch<MailDetail>(endpoint);
        setSelectedMail(detail);
      } catch {
        toast.error("메일을 불러올 수 없습니다.");
      }
    },
    [userId]
  );

  return {
    syncing,
    classifying,
    applyingLabels,
    selectedMail,
    setSelectedMail,
    editingMailId,
    setEditingMailId,
    handleSync,
    handleClassify,
    handleApplyLabels,
    handleUpdateCategory,
    handleSelectMail,
  };
}

import { useState, useCallback } from "react";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";
import type { MailMessage, MailDetail } from "@/features/mail/types";
import type { UserInfo } from "@/features/auth/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ClassifyProgress {
  processed: number;
  total: number;
}

interface UseMailActionsProps {
  userInfo: UserInfo | null;
  sourceFilter: "all" | "gmail" | "naver";
  messages: MailMessage[];
  setMessages: React.Dispatch<React.SetStateAction<MailMessage[]>>;
  loadMessages: (newOffset?: number) => Promise<void>;
  loadCategoryCounts: () => Promise<void>;
  loadFeedbackStats: () => Promise<void>;
}

export function useMailActions({
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
  const [classifyProgress, setClassifyProgress] =
    useState<ClassifyProgress | null>(null);
  const [applyingLabels, setApplyingLabels] = useState(false);
  const [selectedMail, setSelectedMail] = useState<MailDetail | null>(null);
  const [editingMailId, setEditingMailId] = useState<number | null>(null);

  const handleSync = useCallback(async () => {
    if (!userInfo) return;
    setSyncing(true);
    try {
      const promises = [];
      if (userInfo.google_connected) {
        promises.push(
          apiFetch<{ synced: number }>(
            "/api/gmail/sync?max_results=50",
            { method: "POST" }
          )
        );
      }
      if (userInfo.naver_connected) {
        promises.push(
          apiFetch<{ synced: number }>(
            "/api/naver/sync?max_results=50",
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
  }, [userInfo, loadMessages, loadCategoryCounts]);

  const handleClassify = useCallback(async () => {
    setClassifying(true);
    setClassifyProgress(null);

    try {
      const sourceParam =
        sourceFilter === "all" ? "" : `&source=${sourceFilter}`;
      const url = `${API_BASE_URL}/api/classify/mails?${sourceParam}`;

      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Stream not supported");
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let classified = 0;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        // 마지막 줄은 불완전할 수 있으므로 보관
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = JSON.parse(line.slice(6));

          if (data.type === "progress") {
            setClassifyProgress({
              processed: data.processed,
              total: data.total,
            });
          } else if (data.type === "done") {
            classified = data.classified;
          } else if (data.type === "error") {
            throw new Error(data.message);
          }
        }
      }

      toast.success(`${classified}개의 메일이 분류되었습니다.`);
      await loadMessages();
      await loadCategoryCounts();
    } catch (err) {
      toast.error(`분류 실패: ${err}`);
    } finally {
      setClassifying(false);
      setClassifyProgress(null);
    }
  }, [sourceFilter, loadMessages, loadCategoryCounts]);

  const handleApplyLabels = useCallback(async () => {
    const classifiedMails = messages.filter((m) => m.classification);
    if (classifiedMails.length === 0) {
      toast.warning("분류된 메일이 없습니다. 먼저 AI 분류를 실행하세요.");
      return;
    }
    setApplyingLabels(true);
    try {
      const result = await apiFetch<{ applied: number }>(
        "/api/gmail/apply-labels",
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
  }, [messages]);

  const handleUpdateCategory = useCallback(
    async (classificationId: number, newCategory: string, mailId: number) => {
      try {
        await apiFetch("/api/classify/update", {
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
    [selectedMail, setMessages, loadCategoryCounts, loadFeedbackStats]
  );

  const handleSelectMail = useCallback(
    async (mail: MailMessage) => {
      try {
        const endpoint =
          mail.source === "gmail"
            ? `/api/gmail/messages/${mail.id}`
            : `/api/naver/messages/${mail.id}`;
        const detail = await apiFetch<MailDetail>(endpoint);
        setSelectedMail(detail);
      } catch {
        toast.error("메일을 불러올 수 없습니다.");
      }
    },
    []
  );

  return {
    syncing,
    classifying,
    classifyProgress,
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

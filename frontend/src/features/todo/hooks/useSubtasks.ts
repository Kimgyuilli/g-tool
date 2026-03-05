import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { Subtask, SubtaskCreateRequest, SubtasksResponse } from "@/features/todo/types";

interface UseSubtasksOptions {
  userId: number | null;
  taskId: number | null;
}

export function useSubtasks({ userId, taskId }: UseSubtasksOptions) {
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [loading, setLoading] = useState(false);

  const loadSubtasks = useCallback(async () => {
    if (!userId || !taskId) return;
    setLoading(true);
    try {
      const data = await apiFetch<SubtasksResponse>(
        `/api/todo/tasks/${taskId}/subtasks?user_id=${userId}`
      );
      setSubtasks(data.subtasks);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, [userId, taskId]);

  useEffect(() => {
    if (userId && taskId) {
      loadSubtasks();
    } else {
      setSubtasks([]);
    }
  }, [userId, taskId, loadSubtasks]);

  const createSubtask = useCallback(
    async (data: SubtaskCreateRequest) => {
      if (!userId) return null;
      const subtask = await apiFetch<Subtask>(
        `/api/todo/subtasks?user_id=${userId}`,
        { method: "POST", body: JSON.stringify(data) }
      );
      setSubtasks((prev) => [...prev, subtask]);
      return subtask;
    },
    [userId]
  );

  const toggleSubtask = useCallback(
    async (subtaskId: number) => {
      if (!userId) return null;
      // 낙관적 업데이트
      setSubtasks((prev) =>
        prev.map((s) =>
          s.id === subtaskId ? { ...s, is_completed: !s.is_completed } : s
        )
      );
      const subtask = await apiFetch<Subtask>(
        `/api/todo/subtasks/${subtaskId}/toggle?user_id=${userId}`,
        { method: "POST" }
      );
      setSubtasks((prev) =>
        prev.map((s) => (s.id === subtaskId ? subtask : s))
      );
      return subtask;
    },
    [userId]
  );

  const deleteSubtask = useCallback(
    async (subtaskId: number) => {
      if (!userId) return;
      setSubtasks((prev) => prev.filter((s) => s.id !== subtaskId));
      await apiFetch(`/api/todo/subtasks/${subtaskId}?user_id=${userId}`, {
        method: "DELETE",
      });
    },
    [userId]
  );

  return {
    subtasks,
    loading,
    createSubtask,
    toggleSubtask,
    deleteSubtask,
    loadSubtasks,
  };
}

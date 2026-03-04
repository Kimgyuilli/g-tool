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
      setSubtasks([]);
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
      await loadSubtasks();
      return subtask;
    },
    [userId, loadSubtasks]
  );

  const toggleSubtask = useCallback(
    async (subtaskId: number) => {
      if (!userId) return null;
      const subtask = await apiFetch<Subtask>(
        `/api/todo/subtasks/${subtaskId}/toggle?user_id=${userId}`,
        { method: "POST" }
      );
      await loadSubtasks();
      return subtask;
    },
    [userId, loadSubtasks]
  );

  const deleteSubtask = useCallback(
    async (subtaskId: number) => {
      if (!userId) return;
      await apiFetch(`/api/todo/subtasks/${subtaskId}?user_id=${userId}`, {
        method: "DELETE",
      });
      await loadSubtasks();
    },
    [userId, loadSubtasks]
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

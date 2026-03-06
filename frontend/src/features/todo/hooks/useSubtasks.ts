import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { Subtask, SubtaskCreateRequest, SubtasksResponse } from "@/features/todo/types";

interface UseSubtasksOptions {
  taskId: number | null;
}

export function useSubtasks({ taskId }: UseSubtasksOptions) {
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [loading, setLoading] = useState(false);

  const loadSubtasks = useCallback(async () => {
    if (!taskId) return;
    setLoading(true);
    try {
      const data = await apiFetch<SubtasksResponse>(
        `/api/todo/tasks/${taskId}/subtasks`
      );
      setSubtasks(data.subtasks);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    if (taskId) {
      loadSubtasks();
    } else {
      setSubtasks([]);
    }
  }, [taskId, loadSubtasks]);

  const createSubtask = useCallback(
    async (data: SubtaskCreateRequest) => {
      const subtask = await apiFetch<Subtask>("/api/todo/subtasks", {
        method: "POST",
        body: JSON.stringify(data),
      });
      setSubtasks((prev) => [...prev, subtask]);
      return subtask;
    },
    []
  );

  const toggleSubtask = useCallback(async (subtaskId: number) => {
    // 낙관적 업데이트
    setSubtasks((prev) =>
      prev.map((s) =>
        s.id === subtaskId ? { ...s, is_completed: !s.is_completed } : s
      )
    );
    const subtask = await apiFetch<Subtask>(
      `/api/todo/subtasks/${subtaskId}/toggle`,
      { method: "POST" }
    );
    setSubtasks((prev) =>
      prev.map((s) => (s.id === subtaskId ? subtask : s))
    );
    return subtask;
  }, []);

  const deleteSubtask = useCallback(async (subtaskId: number) => {
    setSubtasks((prev) => prev.filter((s) => s.id !== subtaskId));
    await apiFetch(`/api/todo/subtasks/${subtaskId}`, {
      method: "DELETE",
    });
  }, []);

  return {
    subtasks,
    loading,
    createSubtask,
    toggleSubtask,
    deleteSubtask,
    loadSubtasks,
  };
}

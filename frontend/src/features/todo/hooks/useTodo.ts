import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type {
  Task,
  TaskCreateRequest,
  TaskUpdateRequest,
  TasksResponse,
} from "@/features/todo/types";

interface UseTodoOptions {
  userId: number | null;
  enabled?: boolean;
}

export function useTodo({ userId, enabled = true }: UseTodoOptions) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTasks = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const data = await apiFetch<TasksResponse>(
        `/api/todo/tasks?user_id=${userId}`
      );
      setTasks(data.tasks);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (enabled && userId) {
      loadTasks();
    }
  }, [enabled, userId, loadTasks]);

  const createTask = useCallback(
    async (data: TaskCreateRequest) => {
      if (!userId) return null;
      const task = await apiFetch<Task>(
        `/api/todo/tasks?user_id=${userId}`,
        { method: "POST", body: JSON.stringify(data) }
      );
      setTasks((prev) => [...prev, task]);
      return task;
    },
    [userId]
  );

  const updateTask = useCallback(
    async (taskId: number, data: TaskUpdateRequest) => {
      if (!userId) return null;
      const updated = await apiFetch<Task>(
        `/api/todo/tasks/${taskId}?user_id=${userId}`,
        { method: "PATCH", body: JSON.stringify(data) }
      );
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? updated : t))
      );
      return updated;
    },
    [userId]
  );

  const deleteTask = useCallback(
    async (taskId: number) => {
      if (!userId) return;
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      await apiFetch(`/api/todo/tasks/${taskId}?user_id=${userId}`, {
        method: "DELETE",
      });
    },
    [userId]
  );

  const reorderTasks = useCallback(
    async (items: { id: number; position: number; status?: string }[]) => {
      if (!userId) return;
      await apiFetch(`/api/todo/tasks/reorder?user_id=${userId}`, {
        method: "POST",
        body: JSON.stringify({ items }),
      });
    },
    [userId]
  );

  return {
    tasks,
    setTasks,
    loading,
    createTask,
    updateTask,
    deleteTask,
    reorderTasks,
    loadTasks,
  };
}

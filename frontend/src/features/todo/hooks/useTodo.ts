import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type {
  Task,
  TaskCreateRequest,
  TaskUpdateRequest,
  TasksResponse,
} from "@/features/todo/types";

interface UseTodoOptions {
  enabled?: boolean;
}

export function useTodo({ enabled = true }: UseTodoOptions = {}) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<TasksResponse>("/api/todo/tasks");
      setTasks(data.tasks);
    } catch {
      // 에러 시 기존 데이터 보존
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      loadTasks();
    }
  }, [enabled, loadTasks]);

  const createTask = useCallback(
    async (data: TaskCreateRequest) => {
      const task = await apiFetch<Task>("/api/todo/tasks", {
        method: "POST",
        body: JSON.stringify(data),
      });
      setTasks((prev) => [...prev, task]);
      return task;
    },
    []
  );

  const updateTask = useCallback(
    async (taskId: number, data: TaskUpdateRequest) => {
      const updated = await apiFetch<Task>(`/api/todo/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? updated : t))
      );
      return updated;
    },
    []
  );

  const deleteTask = useCallback(async (taskId: number) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    await apiFetch(`/api/todo/tasks/${taskId}`, {
      method: "DELETE",
    });
  }, []);

  const reorderTasks = useCallback(
    async (items: { id: number; position: number; status?: string }[]) => {
      await apiFetch("/api/todo/tasks/reorder", {
        method: "POST",
        body: JSON.stringify({ items }),
      });
    },
    []
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

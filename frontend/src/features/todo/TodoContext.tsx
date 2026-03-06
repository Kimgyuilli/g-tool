"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { useTodo } from "@/features/todo/hooks/useTodo";
import { useSubtasks } from "@/features/todo/hooks/useSubtasks";
import { toast } from "sonner";
import type { Task, Subtask, TaskUpdateRequest } from "@/features/todo/types";

interface TodoContextValue {
  tasks: Task[];
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
  subtasks: Subtask[];
  expandedTaskId: number | null;
  onToggleExpand: (taskId: number) => void;
  onCreateTask: (title: string) => Promise<void>;
  onUpdateTask: (taskId: number, data: TaskUpdateRequest) => Promise<unknown>;
  onDeleteTask: (taskId: number) => Promise<void>;
  onReorderTasks: (items: { id: number; position: number; status?: string }[]) => Promise<void>;
  onCreateSubtask: (title: string) => Promise<void>;
  onToggleSubtask: (subtaskId: number) => Promise<unknown>;
  onDeleteSubtask: (subtaskId: number) => Promise<void>;
}

const TodoCtx = createContext<TodoContextValue | null>(null);

export function useTodoContext() {
  const ctx = useContext(TodoCtx);
  if (!ctx) throw new Error("useTodoContext must be used within TodoProvider");
  return ctx;
}

interface TodoProviderProps {
  children: ReactNode;
}

export function TodoProvider({ children }: TodoProviderProps) {
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null);

  const {
    tasks,
    setTasks,
    createTask,
    updateTask,
    deleteTask,
    reorderTasks,
  } = useTodo({ enabled: true });

  const { subtasks, createSubtask, toggleSubtask, deleteSubtask } =
    useSubtasks({ taskId: expandedTaskId });

  const onToggleExpand = useCallback((taskId: number) => {
    setExpandedTaskId((prev) => (prev === taskId ? null : taskId));
  }, []);

  const onCreateTask = useCallback(async (title: string) => {
    try {
      await createTask({ title });
    } catch {
      toast.error("태스크 생성에 실패했습니다");
    }
  }, [createTask]);

  const onUpdateTask = useCallback(async (taskId: number, data: TaskUpdateRequest) => {
    try {
      return await updateTask(taskId, data);
    } catch {
      toast.error("태스크 수정에 실패했습니다");
      return null;
    }
  }, [updateTask]);

  const onDeleteTask = useCallback(async (taskId: number) => {
    try {
      await deleteTask(taskId);
      if (expandedTaskId === taskId) setExpandedTaskId(null);
      toast.success("태스크가 삭제되었습니다");
    } catch {
      toast.error("태스크 삭제에 실패했습니다");
    }
  }, [deleteTask, expandedTaskId]);

  const onReorderTasks = useCallback(async (items: { id: number; position: number; status?: string }[]) => {
    try {
      await reorderTasks(items);
    } catch {
      toast.error("순서 변경에 실패했습니다");
    }
  }, [reorderTasks]);

  const onCreateSubtask = useCallback(async (title: string) => {
    if (!expandedTaskId) return;
    try {
      await createSubtask({ task_id: expandedTaskId, title });
    } catch {
      toast.error("서브태스크 생성에 실패했습니다");
    }
  }, [createSubtask, expandedTaskId]);

  const onToggleSubtask = useCallback(async (subtaskId: number) => {
    try {
      return await toggleSubtask(subtaskId);
    } catch {
      toast.error("상태 변경에 실패했습니다");
      return null;
    }
  }, [toggleSubtask]);

  const onDeleteSubtask = useCallback(async (subtaskId: number) => {
    try {
      await deleteSubtask(subtaskId);
    } catch {
      toast.error("서브태스크 삭제에 실패했습니다");
    }
  }, [deleteSubtask]);

  return (
    <TodoCtx.Provider
      value={{
        tasks,
        setTasks,
        subtasks,
        expandedTaskId,
        onToggleExpand,
        onCreateTask,
        onUpdateTask,
        onDeleteTask,
        onReorderTasks,
        onCreateSubtask,
        onToggleSubtask,
        onDeleteSubtask,
      }}
    >
      {children}
    </TodoCtx.Provider>
  );
}

"use client";

import { useState, useCallback } from "react";
import { useTodo } from "@/features/todo/hooks/useTodo";
import { useSubtasks } from "@/features/todo/hooks/useSubtasks";
import { KanbanBoard } from "@/features/todo/components/KanbanBoard";
import { toast } from "sonner";

interface TodoPageProps {
  userId: number | null;
}

export function TodoPage({ userId }: TodoPageProps) {
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null);

  const {
    tasks,
    setTasks,
    createTask,
    updateTask,
    deleteTask,
    reorderTasks,
  } = useTodo({ userId, enabled: true });

  const { subtasks, createSubtask, toggleSubtask, deleteSubtask } =
    useSubtasks({ userId, taskId: expandedTaskId });

  const handleToggleExpand = useCallback((taskId: number) => {
    setExpandedTaskId((prev) => (prev === taskId ? null : taskId));
  }, []);

  const handleCreateTask = async (title: string) => {
    try {
      await createTask({ title });
    } catch {
      toast.error("태스크 생성에 실패했습니다");
    }
  };

  const handleUpdateTask = async (taskId: number, data: Parameters<typeof updateTask>[1]) => {
    try {
      return await updateTask(taskId, data);
    } catch {
      toast.error("태스크 수정에 실패했습니다");
      return null;
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    try {
      await deleteTask(taskId);
      if (expandedTaskId === taskId) setExpandedTaskId(null);
      toast.success("태스크가 삭제되었습니다");
    } catch {
      toast.error("태스크 삭제에 실패했습니다");
    }
  };

  const handleReorderTasks = async (items: { id: number; position: number; status?: string }[]) => {
    try {
      await reorderTasks(items);
    } catch {
      toast.error("순서 변경에 실패했습니다");
    }
  };

  const handleCreateSubtask = async (title: string) => {
    if (!expandedTaskId) return;
    try {
      await createSubtask({ task_id: expandedTaskId, title });
    } catch {
      toast.error("서브태스크 생성에 실패했습니다");
    }
  };

  const handleToggleSubtask = async (subtaskId: number) => {
    try {
      return await toggleSubtask(subtaskId);
    } catch {
      toast.error("상태 변경에 실패했습니다");
      return null;
    }
  };

  const handleDeleteSubtask = async (subtaskId: number) => {
    try {
      await deleteSubtask(subtaskId);
    } catch {
      toast.error("서브태스크 삭제에 실패했습니다");
    }
  };

  return (
    <KanbanBoard
      tasks={tasks}
      setTasks={setTasks}
      expandedTaskId={expandedTaskId}
      subtasks={subtasks}
      onToggleExpand={handleToggleExpand}
      onCreateTask={handleCreateTask}
      onUpdateTask={handleUpdateTask}
      onDeleteTask={handleDeleteTask}
      onReorderTasks={handleReorderTasks}
      onCreateSubtask={handleCreateSubtask}
      onToggleSubtask={handleToggleSubtask}
      onDeleteSubtask={handleDeleteSubtask}
    />
  );
}

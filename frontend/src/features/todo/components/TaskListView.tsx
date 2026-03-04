"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Trash2, Calendar as CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Task } from "@/features/todo/types";

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-400",
  medium: "bg-blue-500",
  high: "bg-orange-500",
  urgent: "bg-red-500",
};

interface TaskListViewProps {
  tasks: Task[];
  selectedTaskId: number | null;
  projectName: string;
  onSelectTask: (id: number) => void;
  onCreateTask: (title: string) => void;
  onToggleStatus: (taskId: number, currentStatus: string) => void;
  onDeleteTask: (taskId: number) => void;
}

export function TaskListView({
  tasks,
  selectedTaskId,
  projectName,
  onSelectTask,
  onCreateTask,
  onToggleStatus,
  onDeleteTask,
}: TaskListViewProps) {
  const [quickAdd, setQuickAdd] = useState("");

  const handleQuickAdd = () => {
    const title = quickAdd.trim();
    if (!title) return;
    onCreateTask(title);
    setQuickAdd("");
  };

  const formatDueDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    if (days < 0) return { text: `${Math.abs(days)}일 지남`, className: "text-red-500" };
    if (days === 0) return { text: "오늘", className: "text-orange-500" };
    if (days === 1) return { text: "내일", className: "text-orange-500" };
    const m = date.getMonth() + 1;
    const d = date.getDate();
    return { text: `${m}/${d}`, className: "text-muted-foreground" };
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b">
        <h2 className="text-sm font-semibold mb-2">{projectName}</h2>
        <Input
          placeholder="새 태스크 추가 (Enter)"
          value={quickAdd}
          onChange={(e) => setQuickAdd(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleQuickAdd();
          }}
        />
      </div>

      <div className="flex-1 overflow-auto">
        {tasks.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-8">
            태스크가 없습니다
          </p>
        )}
        {tasks.map((task) => {
          const isDone = task.status === "done";
          return (
            <div
              key={task.id}
              className={cn(
                "group flex items-start gap-2 px-3 py-2 border-b cursor-pointer hover:bg-accent/50",
                selectedTaskId === task.id && "bg-accent"
              )}
              onClick={() => onSelectTask(task.id)}
            >
              <Checkbox
                checked={isDone}
                onCheckedChange={() => onToggleStatus(task.id, task.status)}
                onClick={(e) => e.stopPropagation()}
                className="mt-0.5"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full shrink-0",
                      PRIORITY_COLORS[task.priority] || "bg-gray-400"
                    )}
                  />
                  <span
                    className={cn(
                      "text-sm truncate",
                      isDone && "line-through text-muted-foreground"
                    )}
                  >
                    {task.title}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  {task.due_date && (() => {
                    const { text, className } = formatDueDate(task.due_date);
                    return (
                      <span className={cn("text-xs flex items-center gap-0.5", className)}>
                        <CalendarIcon className="h-3 w-3" />
                        {text}
                      </span>
                    );
                  })()}
                  {task.subtask_count > 0 && (
                    <span className="text-xs text-muted-foreground">
                      {task.subtask_completed}/{task.subtask_count}
                    </span>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100 shrink-0"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteTask(task.id);
                }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

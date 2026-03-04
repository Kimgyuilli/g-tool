"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, ChevronDown, ChevronRight, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { Task, Subtask, TaskUpdateRequest } from "@/features/todo/types";

const PRIORITY_COLORS: Record<string, string> = {
  urgent: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-gray-400",
};

interface KanbanCardProps {
  task: Task;
  isExpanded: boolean;
  subtasks: Subtask[];
  onToggleExpand: () => void;
  onUpdateTask: (taskId: number, data: TaskUpdateRequest) => Promise<unknown>;
  onDeleteTask: (taskId: number) => Promise<void>;
  onCreateSubtask: (title: string) => Promise<void>;
  onToggleSubtask: (subtaskId: number) => Promise<unknown>;
  onDeleteSubtask: (subtaskId: number) => Promise<void>;
}

export function KanbanCard({
  task,
  isExpanded,
  subtasks,
  onToggleExpand,
  onUpdateTask,
  onDeleteTask,
  onCreateSubtask,
  onToggleSubtask,
  onDeleteSubtask,
}: KanbanCardProps) {
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [isEditingDesc, setIsEditingDesc] = useState(false);
  const [descDraft, setDescDraft] = useState(task.description ?? "");

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id, data: { task } });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleSubtaskSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const title = newSubtaskTitle.trim();
    if (!title) return;
    setNewSubtaskTitle("");
    await onCreateSubtask(title);
  };

  const handleDescSave = async () => {
    setIsEditingDesc(false);
    if (descDraft !== (task.description ?? "")) {
      await onUpdateTask(task.id, { description: descDraft });
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-card border rounded-lg shadow-sm group"
    >
      {/* Card header */}
      <div className="flex items-start gap-1 p-3">
        <button
          {...attributes}
          {...listeners}
          className="mt-0.5 cursor-grab opacity-0 group-hover:opacity-50 hover:!opacity-100 touch-none"
        >
          <GripVertical className="h-4 w-4" />
        </button>

        <button onClick={onToggleExpand} className="mt-1 shrink-0">
          {isExpanded ? (
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
          )}
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span
              className={`shrink-0 w-2 h-2 rounded-full ${PRIORITY_COLORS[task.priority]}`}
            />
            <span className="text-sm font-medium truncate">{task.title}</span>
          </div>

          {/* Meta row */}
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            {task.due_date && (
              <span>{new Date(task.due_date).toLocaleDateString("ko-KR", { month: "short", day: "numeric" })}</span>
            )}
            {task.subtask_count > 0 && (
              <span>{task.subtask_completed}/{task.subtask_count}</span>
            )}
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 opacity-0 group-hover:opacity-50 hover:!opacity-100 shrink-0"
          onClick={() => onDeleteTask(task.id)}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>

      {/* Expanded section */}
      {isExpanded && (
        <div className="border-t px-3 pb-3 pt-2 space-y-3">
          {/* Description */}
          <div>
            {isEditingDesc ? (
              <textarea
                className="w-full text-xs border rounded p-2 bg-background resize-none focus:outline-none focus:ring-1 focus:ring-ring"
                rows={3}
                value={descDraft}
                onChange={(e) => setDescDraft(e.target.value)}
                onBlur={handleDescSave}
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setDescDraft(task.description ?? "");
                    setIsEditingDesc(false);
                  }
                }}
                autoFocus
              />
            ) : (
              <p
                className="text-xs text-muted-foreground cursor-pointer hover:text-foreground min-h-[1.5rem]"
                onClick={() => {
                  setDescDraft(task.description ?? "");
                  setIsEditingDesc(true);
                }}
              >
                {task.description || "설명 추가..."}
              </p>
            )}
          </div>

          {/* Subtasks */}
          <div className="space-y-1">
            {subtasks.map((st) => (
              <div key={st.id} className="flex items-center gap-2 group/st">
                <Checkbox
                  checked={st.is_completed}
                  onCheckedChange={() => onToggleSubtask(st.id)}
                  className="h-3.5 w-3.5"
                />
                <span
                  className={`text-xs flex-1 ${st.is_completed ? "line-through text-muted-foreground" : ""}`}
                >
                  {st.title}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 opacity-0 group-hover/st:opacity-100"
                  onClick={() => onDeleteSubtask(st.id)}
                >
                  <Trash2 className="h-2.5 w-2.5" />
                </Button>
              </div>
            ))}

            {/* Add subtask */}
            <form onSubmit={handleSubtaskSubmit} className="flex items-center gap-1">
              <Plus className="h-3 w-3 text-muted-foreground shrink-0" />
              <input
                type="text"
                placeholder="서브태스크 추가..."
                className="text-xs flex-1 bg-transparent outline-none placeholder:text-muted-foreground/50"
                value={newSubtaskTitle}
                onChange={(e) => setNewSubtaskTitle(e.target.value)}
              />
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

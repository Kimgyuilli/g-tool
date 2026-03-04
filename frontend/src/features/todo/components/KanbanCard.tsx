"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Trash2, Plus, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuSeparator,
  ContextMenuTrigger,
  ContextMenuLabel,
} from "@/components/ui/context-menu";
import type { Task, Subtask, TaskUpdateRequest } from "@/features/todo/types";
import {
  STATUS_LABELS,
  STATUS_COLORS,
  PRIORITY_OPTIONS,
} from "@/features/todo/types";
import type { TaskStatus } from "@/features/todo/types";

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

  const isDone = task.status === "done";

  const handleCardClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest("button, input, textarea, [role='checkbox']")) return;
    onToggleExpand();
  };

  const handleToggleDone = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newStatus = isDone ? "todo" : "done";
    onUpdateTask(task.id, { status: newStatus });
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

  const statusKeys = Object.keys(STATUS_LABELS) as TaskStatus[];

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <div
          ref={setNodeRef}
          style={style}
          className={`bg-card border rounded-lg shadow-sm group cursor-pointer transition-colors hover:border-foreground/20 overflow-hidden ${
            isDone ? "opacity-60" : ""
          }`}
          onClick={handleCardClick}
          {...attributes}
          {...listeners}
        >
          {/* Color accent bar */}
          <div
            className={`h-0.5 ${STATUS_COLORS[task.status as TaskStatus] ?? "bg-gray-300"}`}
          />

          {/* Card header */}
          <div className="flex items-start gap-2 p-3">
            {/* Done checkbox */}
            <button
              onClick={handleToggleDone}
              className={`mt-0.5 shrink-0 flex items-center justify-center w-4 h-4 rounded-full border transition-colors ${
                isDone
                  ? "bg-green-500 border-green-500 text-white"
                  : "border-muted-foreground/40 hover:border-green-500"
              }`}
            >
              {isDone && <Check className="h-2.5 w-2.5" />}
            </button>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`shrink-0 w-2 h-2 rounded-full ${PRIORITY_COLORS[task.priority]}`}
                />
                <span
                  className={`text-sm font-medium truncate ${
                    isDone ? "line-through text-muted-foreground" : ""
                  }`}
                >
                  {task.title}
                </span>
              </div>

              {/* Meta row */}
              <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                {task.due_date && (
                  <span>
                    {new Date(task.due_date).toLocaleDateString("ko-KR", {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                )}
                {task.subtask_count > 0 && (
                  <span>
                    {task.subtask_completed}/{task.subtask_count}
                  </span>
                )}
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-50 hover:!opacity-100 shrink-0"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteTask(task.id);
              }}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>

          {/* Expanded section */}
          {isExpanded && (
            <div
              className="border-t px-3 pb-3 pt-2 space-y-3"
              onClick={(e) => e.stopPropagation()}
            >
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
                      className={`text-xs flex-1 ${
                        st.is_completed
                          ? "line-through text-muted-foreground"
                          : ""
                      }`}
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
                <form
                  onSubmit={handleSubtaskSubmit}
                  className="flex items-center gap-1"
                >
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
      </ContextMenuTrigger>

      {/* Right-click context menu */}
      <ContextMenuContent className="w-48">
        <ContextMenuSub>
          <ContextMenuSubTrigger>
            <span className={`w-2 h-2 rounded-full mr-2 ${PRIORITY_COLORS[task.priority]}`} />
            우선순위
          </ContextMenuSubTrigger>
          <ContextMenuSubContent>
            {PRIORITY_OPTIONS.map((opt) => (
              <ContextMenuItem
                key={opt.value}
                onClick={() => onUpdateTask(task.id, { priority: opt.value })}
              >
                <span className={`w-2 h-2 rounded-full mr-2 ${opt.color}`} />
                {opt.label}
                {task.priority === opt.value && (
                  <Check className="ml-auto h-3 w-3" />
                )}
              </ContextMenuItem>
            ))}
          </ContextMenuSubContent>
        </ContextMenuSub>

        <ContextMenuSub>
          <ContextMenuSubTrigger>
            <span className={`w-2 h-2 rounded-full mr-2 ${STATUS_COLORS[task.status as TaskStatus]}`} />
            상태 변경
          </ContextMenuSubTrigger>
          <ContextMenuSubContent>
            {statusKeys.map((s) => (
              <ContextMenuItem
                key={s}
                onClick={() => onUpdateTask(task.id, { status: s })}
              >
                <span className={`w-2 h-2 rounded-full mr-2 ${STATUS_COLORS[s]}`} />
                {STATUS_LABELS[s]}
                {task.status === s && (
                  <Check className="ml-auto h-3 w-3" />
                )}
              </ContextMenuItem>
            ))}
          </ContextMenuSubContent>
        </ContextMenuSub>

        <ContextMenuSeparator />

        <ContextMenuLabel>
          {PRIORITY_OPTIONS.find((p) => p.value === task.priority)?.label ?? "보통"} 우선순위
        </ContextMenuLabel>

        <ContextMenuSeparator />

        <ContextMenuItem
          className="text-destructive focus:text-destructive"
          onClick={() => onDeleteTask(task.id)}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          삭제
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}

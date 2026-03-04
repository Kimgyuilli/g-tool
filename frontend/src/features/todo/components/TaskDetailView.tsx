"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { X, Plus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Task, Subtask, TaskUpdateRequest } from "@/features/todo/types";

const STATUS_LABELS: Record<string, string> = {
  todo: "할 일",
  in_progress: "진행 중",
  done: "완료",
};

const PRIORITY_LABELS: Record<string, string> = {
  low: "낮음",
  medium: "보통",
  high: "높음",
  urgent: "긴급",
};

const PRIORITY_VARIANTS: Record<string, "secondary" | "default" | "destructive" | "outline"> = {
  low: "secondary",
  medium: "outline",
  high: "default",
  urgent: "destructive",
};

interface TaskDetailViewProps {
  task: Task;
  subtasks: Subtask[];
  onClose: () => void;
  onUpdateTask: (taskId: number, data: TaskUpdateRequest) => void;
  onCreateSubtask: (title: string) => void;
  onToggleSubtask: (subtaskId: number) => void;
  onDeleteSubtask: (subtaskId: number) => void;
}

export function TaskDetailView({
  task,
  subtasks,
  onClose,
  onUpdateTask,
  onCreateSubtask,
  onToggleSubtask,
  onDeleteSubtask,
}: TaskDetailViewProps) {
  const [newSubtask, setNewSubtask] = useState("");
  const [editingDescription, setEditingDescription] = useState(false);
  const [descDraft, setDescDraft] = useState(task.description || "");

  const handleAddSubtask = () => {
    const title = newSubtask.trim();
    if (!title) return;
    onCreateSubtask(title);
    setNewSubtask("");
  };

  const handleSaveDescription = () => {
    onUpdateTask(task.id, { description: descDraft });
    setEditingDescription(false);
  };

  const cycleStatus = () => {
    const order = ["todo", "in_progress", "done"];
    const idx = order.indexOf(task.status);
    const next = order[(idx + 1) % order.length];
    onUpdateTask(task.id, { status: next });
  };

  const cyclePriority = () => {
    const order = ["low", "medium", "high", "urgent"];
    const idx = order.indexOf(task.priority);
    const next = order[(idx + 1) % order.length];
    onUpdateTask(task.id, { priority: next });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="text-sm font-semibold truncate">{task.title}</h3>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-4">
        {/* Status & Priority */}
        <div className="flex gap-2">
          <Badge
            variant="outline"
            className="cursor-pointer"
            onClick={cycleStatus}
          >
            {STATUS_LABELS[task.status] || task.status}
          </Badge>
          <Badge
            variant={PRIORITY_VARIANTS[task.priority] || "secondary"}
            className="cursor-pointer"
            onClick={cyclePriority}
          >
            {PRIORITY_LABELS[task.priority] || task.priority}
          </Badge>
        </div>

        {/* Description */}
        <div>
          <p className="text-xs text-muted-foreground mb-1">설명</p>
          {editingDescription ? (
            <div className="space-y-1">
              <Textarea
                value={descDraft}
                onChange={(e) => setDescDraft(e.target.value)}
                rows={3}
                autoFocus
              />
              <div className="flex gap-1">
                <Button size="sm" variant="default" onClick={handleSaveDescription}>
                  저장
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setEditingDescription(false);
                    setDescDraft(task.description || "");
                  }}
                >
                  취소
                </Button>
              </div>
            </div>
          ) : (
            <p
              className={cn(
                "text-sm cursor-pointer rounded p-1 hover:bg-accent min-h-[2rem]",
                !task.description && "text-muted-foreground italic"
              )}
              onClick={() => {
                setDescDraft(task.description || "");
                setEditingDescription(true);
              }}
            >
              {task.description || "클릭하여 설명 추가"}
            </p>
          )}
        </div>

        {/* Subtasks */}
        <div>
          <p className="text-xs text-muted-foreground mb-1">
            서브태스크 ({subtasks.filter((s) => s.is_completed).length}/
            {subtasks.length})
          </p>
          <div className="space-y-1">
            {subtasks.map((sub) => (
              <div
                key={sub.id}
                className="group flex items-center gap-2 rounded px-1 py-0.5 hover:bg-accent"
              >
                <Checkbox
                  checked={sub.is_completed}
                  onCheckedChange={() => onToggleSubtask(sub.id)}
                />
                <span
                  className={cn(
                    "flex-1 text-sm",
                    sub.is_completed && "line-through text-muted-foreground"
                  )}
                >
                  {sub.title}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 opacity-0 group-hover:opacity-100"
                  onClick={() => onDeleteSubtask(sub.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-1 mt-2">
            <Plus className="h-3 w-3 text-muted-foreground" />
            <Input
              placeholder="서브태스크 추가"
              className="h-7 text-sm"
              value={newSubtask}
              onChange={(e) => setNewSubtask(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAddSubtask();
              }}
            />
          </div>
        </div>

        {/* Metadata */}
        <div className="text-xs text-muted-foreground space-y-0.5 pt-2 border-t">
          {task.due_date && (
            <p>마감일: {new Date(task.due_date).toLocaleDateString("ko-KR")}</p>
          )}
          {task.created_at && (
            <p>생성: {new Date(task.created_at).toLocaleString("ko-KR")}</p>
          )}
          {task.updated_at && (
            <p>수정: {new Date(task.updated_at).toLocaleString("ko-KR")}</p>
          )}
        </div>
      </div>
    </div>
  );
}

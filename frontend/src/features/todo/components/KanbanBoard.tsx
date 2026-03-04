"use client";

import { useState, useMemo } from "react";
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { useDroppable } from "@dnd-kit/core";
import { Plus } from "lucide-react";
import { KanbanCard } from "./KanbanCard";
import type {
  Task,
  Subtask,
  TaskStatus,
  TaskUpdateRequest,
} from "@/features/todo/types";
import {
  STATUS_LABELS,
  STATUS_COLORS,
  STATUS_BG,
  PRIORITY_MAP,
} from "@/features/todo/types";

const COLUMNS: TaskStatus[] = ["todo", "in_progress", "on_hold", "done"];

interface KanbanBoardProps {
  tasks: Task[];
  setTasks: React.Dispatch<React.SetStateAction<Task[]>>;
  expandedTaskId: number | null;
  subtasks: Subtask[];
  onToggleExpand: (taskId: number) => void;
  onCreateTask: (title: string) => Promise<void>;
  onUpdateTask: (taskId: number, data: TaskUpdateRequest) => Promise<unknown>;
  onDeleteTask: (taskId: number) => Promise<void>;
  onReorderTasks: (items: { id: number; position: number; status?: string }[]) => Promise<void>;
  onCreateSubtask: (title: string) => Promise<void>;
  onToggleSubtask: (subtaskId: number) => Promise<unknown>;
  onDeleteSubtask: (subtaskId: number) => Promise<void>;
}

function DroppableColumn({
  status,
  children,
}: {
  status: TaskStatus;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: `column-${status}` });

  return (
    <div
      ref={setNodeRef}
      className={`flex-1 min-h-[200px] p-2 space-y-2 rounded-lg transition-colors ${
        isOver ? "bg-accent/50" : ""
      }`}
    >
      {children}
    </div>
  );
}

export function KanbanBoard({
  tasks,
  setTasks,
  expandedTaskId,
  subtasks,
  onToggleExpand,
  onCreateTask,
  onUpdateTask,
  onDeleteTask,
  onReorderTasks,
  onCreateSubtask,
  onToggleSubtask,
  onDeleteSubtask,
}: KanbanBoardProps) {
  const [quickAddValue, setQuickAddValue] = useState("");
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  const columnTasks = useMemo(() => {
    const grouped: Record<TaskStatus, Task[]> = {
      todo: [],
      in_progress: [],
      on_hold: [],
      done: [],
    };
    for (const t of tasks) {
      const col = grouped[t.status as TaskStatus];
      if (col) col.push(t);
    }
    return grouped;
  }, [tasks]);

  const findColumn = (id: string | number): TaskStatus | null => {
    // Check if it's a column id
    for (const col of COLUMNS) {
      if (id === `column-${col}`) return col;
    }
    // Check if it's a task id
    const task = tasks.find((t) => t.id === id);
    return task ? (task.status as TaskStatus) : null;
  };

  const handleDragStart = (event: DragStartEvent) => {
    const task = tasks.find((t) => t.id === event.active.id);
    if (task) setActiveTask(task);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as number;
    const overId = over.id;

    const activeCol = findColumn(activeId);
    const overCol = findColumn(overId);

    if (!activeCol || !overCol || activeCol === overCol) return;

    // Move task to new column optimistically
    setTasks((prev) =>
      prev.map((t) =>
        t.id === activeId ? { ...t, status: overCol } : t
      )
    );
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as number;
    const overId = over.id;
    const targetCol = findColumn(overId);

    if (!targetCol) return;

    // Get tasks in the target column (with the moved task already in it)
    let colTasks = tasks.filter(
      (t) => t.status === targetCol || t.id === activeId
    );
    // Deduplicate & ensure moved task has the right status
    colTasks = colTasks
      .map((t) => (t.id === activeId ? { ...t, status: targetCol } : t))
      .filter(
        (t, i, arr) => arr.findIndex((x) => x.id === t.id) === i
      );

    // Handle same-column reorder
    if (typeof overId === "number" && overId !== activeId) {
      const oldIndex = colTasks.findIndex((t) => t.id === activeId);
      const newIndex = colTasks.findIndex((t) => t.id === overId);
      if (oldIndex !== -1 && newIndex !== -1) {
        colTasks = arrayMove(colTasks, oldIndex, newIndex);
      }
    }

    // Optimistic UI update for ordering
    setTasks((prev) => {
      const others = prev.filter(
        (t) => t.status !== targetCol && t.id !== activeId
      );
      return [
        ...others,
        ...colTasks.map((t, i) => ({
          ...t,
          status: targetCol,
          position: i + 1,
        })),
      ];
    });

    const items = colTasks.map((t, i) => ({
      id: t.id,
      position: i + 1,
      status: targetCol,
    }));

    await onReorderTasks(items);
  };

  const handleQuickAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const title = quickAddValue.trim();
    if (!title) return;
    setQuickAddValue("");
    await onCreateTask(title);
  };

  return (
    <div className="flex-1 overflow-auto p-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 h-full min-h-0">
          {COLUMNS.map((status) => {
            const colTasks = columnTasks[status];
            return (
              <div
                key={status}
                className={`flex-1 min-w-[280px] flex flex-col rounded-xl ${STATUS_BG[status]}`}
              >
                {/* Column header */}
                <div className="flex items-center justify-between px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${STATUS_COLORS[status]}`} />
                    <h3 className="text-sm font-semibold">
                      {STATUS_LABELS[status]}
                    </h3>
                    <span className="text-xs text-muted-foreground bg-muted rounded-full px-2 py-0.5">
                      {colTasks.length}
                    </span>
                  </div>
                </div>

                {/* Quick add (only for "todo" column) */}
                {status === "todo" && (
                  <form onSubmit={handleQuickAdd} className="px-3 pb-2">
                    <div className="flex items-center gap-2 border rounded-lg bg-background px-3 py-2">
                      <Plus className="h-4 w-4 text-muted-foreground shrink-0" />
                      <input
                        type="text"
                        placeholder="새 할 일 추가..."
                        className="text-sm flex-1 bg-transparent outline-none placeholder:text-muted-foreground/60"
                        value={quickAddValue}
                        onChange={(e) => setQuickAddValue(e.target.value)}
                      />
                    </div>
                  </form>
                )}

                {/* Task cards */}
                <DroppableColumn status={status}>
                  <SortableContext
                    items={colTasks.map((t) => t.id)}
                    strategy={verticalListSortingStrategy}
                  >
                    {colTasks.map((task) => (
                      <KanbanCard
                        key={task.id}
                        task={task}
                        isExpanded={expandedTaskId === task.id}
                        subtasks={expandedTaskId === task.id ? subtasks : []}
                        onToggleExpand={() => onToggleExpand(task.id)}
                        onUpdateTask={onUpdateTask}
                        onDeleteTask={onDeleteTask}
                        onCreateSubtask={onCreateSubtask}
                        onToggleSubtask={onToggleSubtask}
                        onDeleteSubtask={onDeleteSubtask}
                      />
                    ))}
                  </SortableContext>
                </DroppableColumn>
              </div>
            );
          })}
        </div>

        <DragOverlay>
          {activeTask && (
            <div className="bg-card border rounded-lg shadow-lg p-3 opacity-90">
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    PRIORITY_MAP[activeTask.priority]?.badgeCls ?? ""
                  }`}
                >
                  {PRIORITY_MAP[activeTask.priority]?.badge ?? "P2"}
                </span>
                <span className="text-sm font-medium">{activeTask.title}</span>
              </div>
            </div>
          )}
        </DragOverlay>
      </DndContext>
    </div>
  );
}

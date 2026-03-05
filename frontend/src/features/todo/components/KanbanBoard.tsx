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
import type { Task, TaskStatus } from "@/features/todo/types";
import {
  STATUS_LABELS,
  STATUS_COLORS,
  STATUS_BG,
  PRIORITY_MAP,
} from "@/features/todo/types";
import { useTodoContext } from "@/features/todo/TodoContext";

const COLUMNS: TaskStatus[] = ["todo", "in_progress", "on_hold", "done"];

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

export function KanbanBoard() {
  const {
    tasks,
    setTasks,
    onCreateTask,
    onReorderTasks,
  } = useTodoContext();

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
    for (const col of COLUMNS) {
      if (id === `column-${col}`) return col;
    }
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
    const overCol = findColumn(over.id);
    const activeCol = findColumn(activeId);

    if (!activeCol || !overCol || activeCol === overCol) return;

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
    const targetCol = findColumn(over.id) ?? findColumn(activeId);
    if (!targetCol) return;

    // 현재 tasks state에서 해당 컬럼의 태스크 목록
    let colTasks = tasks.filter((t) => t.status === targetCol);

    // 같은 컬럼 내 순서 변경
    if (typeof over.id === "number" && over.id !== activeId) {
      const oldIdx = colTasks.findIndex((t) => t.id === activeId);
      const newIdx = colTasks.findIndex((t) => t.id === over.id);
      if (oldIdx !== -1 && newIdx !== -1) {
        colTasks = arrayMove(colTasks, oldIdx, newIdx);
      }
    }

    // position 재할당 & 낙관적 UI 업데이트
    const reordered = colTasks.map((t, i) => ({
      ...t,
      position: i + 1,
    }));

    setTasks((prev) => {
      const others = prev.filter((t) => t.status !== targetCol);
      return [...others, ...reordered];
    });

    const items = reordered.map((t) => ({
      id: t.id,
      position: t.position,
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
                      <KanbanCard key={task.id} task={task} />
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

export interface Task {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "on_hold" | "done";
  priority: "low" | "medium" | "high" | "urgent";
  due_date: string | null;
  position: number;
  subtask_count: number;
  subtask_completed: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface Subtask {
  id: number;
  task_id: number;
  title: string;
  is_completed: boolean;
  position: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskCreateRequest {
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
}

export interface TaskUpdateRequest {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string | null;
}

export interface SubtaskCreateRequest {
  task_id: number;
  title: string;
}

export interface TasksResponse {
  tasks: Task[];
}

export interface SubtasksResponse {
  subtasks: Subtask[];
}

export type TaskStatus = "todo" | "in_progress" | "on_hold" | "done";

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: "할 일",
  in_progress: "진행 중",
  on_hold: "보류",
  done: "완료",
};

export const STATUS_COLORS: Record<TaskStatus, string> = {
  todo: "bg-blue-500",
  in_progress: "bg-amber-500",
  on_hold: "bg-gray-400",
  done: "bg-green-500",
};

/** 컬럼 배경 틴트 */
export const STATUS_BG: Record<TaskStatus, string> = {
  todo: "bg-blue-500/5",
  in_progress: "bg-amber-500/5",
  on_hold: "bg-gray-500/5",
  done: "bg-green-500/5",
};

export type TaskPriority = "urgent" | "high" | "medium" | "low";

export const PRIORITY_OPTIONS: {
  value: TaskPriority;
  label: string;
  badge: string;
  color: string;
  badgeCls: string;
}[] = [
  {
    value: "urgent",
    label: "긴급",
    badge: "P0",
    color: "bg-red-500",
    badgeCls: "bg-red-500/15 text-red-600 dark:text-red-400",
  },
  {
    value: "high",
    label: "높음",
    badge: "P1",
    color: "bg-orange-500",
    badgeCls: "bg-orange-500/15 text-orange-600 dark:text-orange-400",
  },
  {
    value: "medium",
    label: "보통",
    badge: "P2",
    color: "bg-yellow-500",
    badgeCls: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400",
  },
  {
    value: "low",
    label: "낮음",
    badge: "P3",
    color: "bg-gray-400",
    badgeCls: "bg-gray-400/15 text-gray-500 dark:text-gray-400",
  },
];

export const PRIORITY_MAP = Object.fromEntries(
  PRIORITY_OPTIONS.map((p) => [p.value, p])
) as Record<TaskPriority, (typeof PRIORITY_OPTIONS)[number]>;

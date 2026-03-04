export interface Task {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "on_hold";
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

export type TaskStatus = "todo" | "in_progress" | "on_hold";

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: "할 일",
  in_progress: "진행 중",
  on_hold: "보류",
};

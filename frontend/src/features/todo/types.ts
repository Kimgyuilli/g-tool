export interface Project {
  id: number;
  name: string;
  description: string | null;
  color: string | null;
  position: number;
  task_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface Task {
  id: number;
  project_id: number;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "done";
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

export interface ProjectCreateRequest {
  name: string;
  description?: string;
  color?: string;
}

export interface TaskCreateRequest {
  project_id: number;
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
  project_id?: number;
}

export interface SubtaskCreateRequest {
  task_id: number;
  title: string;
}

export interface ProjectsResponse {
  projects: Project[];
}

export interface TasksResponse {
  tasks: Task[];
}

export interface SubtasksResponse {
  subtasks: Subtask[];
}

export interface Project {
  projectId: string;
  name: string;
  description?: string;
  deadline?: string;
  objective?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectListResponse {
  projects: Project[];
  count: number;
}

export interface Task {
  taskId: string;
  projectId: string;
  title: string;
  description?: string;
  deadline?: string;
  status: "pending" | "in_progress" | "completed";
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface TaskListResponse {
  tasks: Task[];
  count: number;
}

export interface PrioritizedTask {
  taskId: string;
  title: string;
  priorityScore: number;
  quadrant:
    | "urgent-important"
    | "urgent-not-important"
    | "not-urgent-important"
    | "not-urgent-not-important";
  reason: string;
  nextAction: string;
  dependencies: string[];
  confidence: number;
}

export interface PrioritizationResponse {
  projectId: string;
  recommendations: PrioritizedTask[];
  summary: string;
  generatedAt: string;
}

export type ProjectCreate = Pick<Project, "name"> &
  Partial<Pick<Project, "description" | "deadline" | "objective">>;

export type ProjectUpdate = Partial<ProjectCreate>;

export type TaskCreate = Pick<Task, "title"> &
  Partial<Pick<Task, "description" | "deadline" | "status">>;

export type TaskUpdate = Partial<Pick<Task, "title" | "description" | "deadline" | "status">>;

// Generate Tasks
export interface SuggestedTask {
  title: string;
  description: string;
  deadline: string | null;
  reason: string;
  order: number;
}

export interface GenerateTasksResponse {
  projectId: string;
  suggestions: SuggestedTask[];
  strategy: string;
  generatedAt: string;
}

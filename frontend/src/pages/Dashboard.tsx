import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CalendarClock,
  FolderKanban,
  ListTodo,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAllTasks, useProjects } from "@/hooks/use-api";
import { prioritizeApi } from "@/lib/api";
import type { PrioritizationResponse, PrioritizedTask, Task } from "@/types";

const PROJECT_COLORS = [
  "bg-blue-500/20 text-blue-400 border-blue-500/30",
  "bg-purple-500/20 text-purple-400 border-purple-500/30",
  "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  "bg-amber-500/20 text-amber-400 border-amber-500/30",
  "bg-rose-500/20 text-rose-400 border-rose-500/30",
  "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  "bg-orange-500/20 text-orange-400 border-orange-500/30",
  "bg-pink-500/20 text-pink-400 border-pink-500/30",
];

function getDaysUntil(deadline: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const due = new Date(deadline + "T00:00:00");
  return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

type QuadrantKey =
  | "urgent-important"
  | "urgent-not-important"
  | "not-urgent-important"
  | "not-urgent-not-important";

const QUADRANT_META: Record<
  QuadrantKey,
  { label: string; description: string; className: string }
> = {
  "urgent-important": {
    label: "Do First",
    description: "Urgent & Important",
    className: "border-red-500/30 bg-red-500/5",
  },
  "not-urgent-important": {
    label: "Schedule",
    description: "Not Urgent & Important",
    className: "border-blue-500/30 bg-blue-500/5",
  },
  "urgent-not-important": {
    label: "Quick Wins",
    description: "Urgent & Not Important",
    className: "border-amber-500/30 bg-amber-500/5",
  },
  "not-urgent-not-important": {
    label: "Consider Dropping",
    description: "Not Urgent & Not Important",
    className: "border-muted-foreground/20 bg-muted/30",
  },
};

interface TaskWithMeta {
  task: Task;
  projectName: string;
  projectColor: string;
  priority?: PrioritizedTask;
}

export function Dashboard() {
  const { data: projectsData, isLoading: projectsLoading } = useProjects();
  const projects = useMemo(
    () => projectsData?.projects ?? [],
    [projectsData]
  );
  const projectIds = useMemo(
    () => projects.map((p) => p.projectId),
    [projects]
  );

  const taskQueries = useAllTasks(projectIds);
  const tasksLoading = taskQueries.some((q) => q.isLoading);

  const [prioritizations, setPrioritizations] = useState<
    Record<string, PrioritizationResponse>
  >({});
  const hasFetchedRef = useRef(false);

  // Build colour map
  const projectColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    projects.forEach((p, i) => {
      map[p.projectId] = PROJECT_COLORS[i % PROJECT_COLORS.length];
    });
    return map;
  }, [projects]);

  // Flatten all active tasks
  const allTasks: TaskWithMeta[] = useMemo(() => {
    const result: TaskWithMeta[] = [];
    taskQueries.forEach((q, i) => {
      if (!q.data) return;
      const project = projects[i];
      if (!project) return;
      q.data.tasks.forEach((task) => {
        if (task.status === "completed") return;
        const pri = prioritizations[project.projectId]?.recommendations.find(
          (r) => r.taskId === task.taskId
        );
        result.push({
          task,
          projectName: project.name,
          projectColor:
            projectColorMap[project.projectId] ?? PROJECT_COLORS[0],
          priority: pri,
        });
      });
    });
    return result;
  }, [taskQueries, projects, prioritizations, projectColorMap]);

  // Auto-prioritize once tasks are loaded
  useEffect(() => {
    if (hasFetchedRef.current) return;
    if (tasksLoading || allTasks.length === 0 || projects.length === 0) return;

    hasFetchedRef.current = true;
    (async () => {
      const results: Record<string, PrioritizationResponse> = {};
      for (const project of projects) {
        const hasTasks = allTasks.some(
          (t) => t.task.projectId === project.projectId
        );
        if (!hasTasks) continue;
        try {
          const res = await prioritizeApi.run(project.projectId);
          results[project.projectId] = res;
        } catch {
          // Use heuristic fallback
        }
      }
      if (Object.keys(results).length > 0) {
        setPrioritizations(results);
      }
    })();
  }, [tasksLoading, allTasks, projects]);

  // Tasks due within 3 days
  const urgentTasks = useMemo(() => {
    return allTasks
      .filter((t) => {
        if (!t.task.deadline) return false;
        const days = getDaysUntil(t.task.deadline);
        return days >= 0 && days <= 3;
      })
      .sort(
        (a, b) =>
          getDaysUntil(a.task.deadline!) - getDaysUntil(b.task.deadline!)
      );
  }, [allTasks]);

  // Group into quadrants — only tasks with AI prioritization
  const quadrants = useMemo(() => {
    const grouped: Record<QuadrantKey, TaskWithMeta[]> = {
      "urgent-important": [],
      "not-urgent-important": [],
      "urgent-not-important": [],
      "not-urgent-not-important": [],
    };
    allTasks.forEach((t) => {
      if (t.priority) {
        grouped[t.priority.quadrant as QuadrantKey].push(t);
      }
    });
    Object.values(grouped).forEach((arr) =>
      arr.sort(
        (a, b) =>
          (b.priority?.priorityScore ?? 0) -
          (a.priority?.priorityScore ?? 0)
      )
    );
    return grouped;
  }, [allTasks]);

  const totalActiveTasks = allTasks.length;

  return (
    <div className="space-y-6">
      {/* Scrolling Deadline Banner */}
      {urgentTasks.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-amber-500/20">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            <span className="text-xs font-medium text-amber-400">
              Due Soon
            </span>
          </div>
          <div className="relative overflow-hidden py-2.5 px-4">
            <div className="animate-marquee flex gap-8 whitespace-nowrap">
              {[...urgentTasks, ...urgentTasks].map((t, idx) => {
                const days = getDaysUntil(t.task.deadline!);
                const urgencyText =
                  days === 0
                    ? "TODAY"
                    : days === 1
                      ? "TOMORROW"
                      : `${days}d left`;
                return (
                  <span
                    key={`${t.task.taskId}-${idx}`}
                    className="inline-flex items-center gap-2 text-sm"
                  >
                    <span
                      className={`inline-block h-2 w-2 rounded-full shrink-0 ${t.projectColor.split(" ")[0]}`}
                    />
                    <span className="text-foreground font-medium">
                      {t.task.title}
                    </span>
                    <span className="text-muted-foreground">
                      {t.projectName}
                    </span>
                    <span
                      className={`text-xs font-semibold ${days === 0 ? "text-red-400" : "text-amber-400"}`}
                    >
                      <CalendarClock className="inline h-3 w-3 mr-0.5" />
                      {urgencyText}
                    </span>
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-muted-foreground">
            Turn priorities into progress.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link to="/projects/new">
            <Plus className="h-4 w-4" />
            New Project
          </Link>
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Projects
            </CardTitle>
            <FolderKanban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {projectsLoading ? "—" : projects.length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Tasks
            </CardTitle>
            <ListTodo className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {tasksLoading ? "—" : totalActiveTasks}
            </div>
            <p className="text-xs text-muted-foreground">
              across all projects
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Due Soon
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{urgentTasks.length}</div>
            <p className="text-xs text-muted-foreground">within 3 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Eisenhower Matrix — Always Visible */}
      <div className="space-y-3">
        <h2 className="text-lg font-medium">Eisenhower Matrix</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {(
            [
              "urgent-important",
              "not-urgent-important",
              "urgent-not-important",
              "not-urgent-not-important",
            ] as QuadrantKey[]
          ).map((key) => {
            const meta = QUADRANT_META[key];
            const items = quadrants[key];
            return (
              <Card
                key={key}
                className={`border ${meta.className} min-h-[160px]`}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">
                    {meta.label}
                    <span className="ml-2 text-xs font-normal text-muted-foreground">
                      {meta.description}
                    </span>
                    {items.length > 0 && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({items.length})
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-1.5">
                  {items.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic py-4 text-center">
                      No tasks
                    </p>
                  ) : (
                    items.map((t) => (
                      <div
                        key={t.task.taskId}
                        className="flex items-center gap-2 text-sm"
                      >
                        <span
                          className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs shrink-0 ${t.projectColor}`}
                        >
                          {t.projectName}
                        </span>
                        <span className="text-foreground truncate">
                          {t.task.title}
                        </span>
                        {t.priority && (
                          <span className="ml-auto text-xs text-muted-foreground whitespace-nowrap">
                            {t.priority.priorityScore}
                          </span>
                        )}
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Project Legend */}
      {projects.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {projects.map((p, i) => (
            <Link
              key={p.projectId}
              to={`/projects/${p.projectId}`}
              className={`inline-flex items-center rounded-md border px-2 py-1 text-xs transition-opacity hover:opacity-80 ${PROJECT_COLORS[i % PROJECT_COLORS.length]}`}
            >
              {p.name}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CalendarClock,
  FolderKanban,
  ListTodo,
  Loader2,
  Plus,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAllTasks, useProjects } from "@/hooks/use-api";
import { prioritizeApi } from "@/lib/api";
import type { PrioritizationResponse, PrioritizedTask, Task } from "@/types";

// Project colour palette — distinct, accessible on dark bg
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
  const projects = useMemo(() => projectsData?.projects ?? [], [projectsData]);
  const projectIds = useMemo(() => projects.map((p) => p.projectId), [projects]);

  const taskQueries = useAllTasks(projectIds);
  const tasksLoading = taskQueries.some((q) => q.isLoading);

  const [prioritizations, setPrioritizations] = useState<
    Record<string, PrioritizationResponse>
  >({});
  const [isPrioritizing, setIsPrioritizing] = useState(false);

  // Build colour map for projects
  const projectColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    projects.forEach((p, i) => {
      map[p.projectId] = PROJECT_COLORS[i % PROJECT_COLORS.length];
    });
    return map;
  }, [projects]);

  // Flatten all tasks with project metadata
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
          projectColor: projectColorMap[project.projectId] ?? PROJECT_COLORS[0],
          priority: pri,
        });
      });
    });
    return result;
  }, [taskQueries, projects, prioritizations, projectColorMap]);

  // Tasks approaching deadline (within 3 days)
  const urgentTasks = useMemo(() => {
    return allTasks
      .filter((t) => {
        if (!t.task.deadline) return false;
        const days = getDaysUntil(t.task.deadline);
        return days >= 0 && days <= 3;
      })
      .sort((a, b) => getDaysUntil(a.task.deadline!) - getDaysUntil(b.task.deadline!));
  }, [allTasks]);

  // Group by quadrant
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
    // Sort each quadrant by priority score desc
    Object.values(grouped).forEach((arr) =>
      arr.sort((a, b) => (b.priority?.priorityScore ?? 0) - (a.priority?.priorityScore ?? 0))
    );
    return grouped;
  }, [allTasks]);

  const hasPrioritizations = Object.keys(prioritizations).length > 0;
  const totalActiveTasks = allTasks.length;

  // Prioritize all projects
  const handlePrioritizeAll = async () => {
    setIsPrioritizing(true);
    const results: Record<string, PrioritizationResponse> = {};
    for (const project of projects) {
      const projectTasks = allTasks.filter(
        (t) => t.task.projectId === project.projectId
      );
      if (projectTasks.length === 0) continue;
      try {
        const res = await prioritizeApi.run(project.projectId);
        results[project.projectId] = res;
      } catch {
        // Skip projects that fail
      }
    }
    setPrioritizations(results);
    setIsPrioritizing(false);
  };

  return (
    <div className="space-y-6">
      {/* Deadline Banner */}
      {urgentTasks.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <span className="text-sm font-medium text-amber-400">
              Tasks Due Soon
            </span>
          </div>
          <div className="space-y-1.5">
            {urgentTasks.map((t) => {
              const days = getDaysUntil(t.task.deadline!);
              const urgencyText =
                days === 0
                  ? "Due today"
                  : days === 1
                    ? "Due tomorrow"
                    : `Due in ${days} days`;
              return (
                <div
                  key={t.task.taskId}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${t.projectColor.split(" ")[0]}`}
                    />
                    <span className="text-foreground">{t.task.title}</span>
                    <span className="text-muted-foreground">
                      · {t.projectName}
                    </span>
                  </div>
                  <Badge
                    variant={days === 0 ? "destructive" : "warning"}
                    className="text-xs"
                  >
                    <CalendarClock className="h-3 w-3 mr-1" />
                    {urgencyText}
                  </Badge>
                </div>
              );
            })}
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
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/projects/new">
              <Plus className="h-4 w-4" />
              New Project
            </Link>
          </Button>
          <Button
            onClick={handlePrioritizeAll}
            disabled={isPrioritizing || totalActiveTasks === 0}
          >
            {isPrioritizing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Prioritize All
          </Button>
        </div>
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
            <p className="text-xs text-muted-foreground">across all projects</p>
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

      {/* Eisenhower Matrix */}
      {hasPrioritizations ? (
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
                  className={`border ${meta.className} min-h-[140px]`}
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">
                      {meta.label}
                      <span className="ml-2 text-xs font-normal text-muted-foreground">
                        {meta.description}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-1.5">
                    {items.length === 0 ? (
                      <p className="text-xs text-muted-foreground italic">
                        No tasks in this quadrant
                      </p>
                    ) : (
                      items.map((t) => (
                        <div
                          key={t.task.taskId}
                          className="flex items-center gap-2 text-sm"
                        >
                          <span
                            className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs ${t.projectColor}`}
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
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Sparkles className="h-10 w-10 text-muted-foreground/40" />
            <p className="mt-4 text-lg font-medium text-muted-foreground">
              Eisenhower Matrix
            </p>
            <p className="text-sm text-muted-foreground text-center max-w-sm">
              Click "Prioritize All" to have M1 analyze your tasks and place
              them in the matrix.
            </p>
          </CardContent>
        </Card>
      )}

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

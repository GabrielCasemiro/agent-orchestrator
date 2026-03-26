"use client";

import { useState } from "react";
import { Task, Agent } from "@/lib/api";
import TaskDetail from "./TaskDetail";

const columns = [
  {
    key: "pending",
    label: "Queued",
    color: "var(--color-status-pending)",
    glow: "rgba(96, 96, 120, 0.08)",
  },
  {
    key: "in_progress",
    label: "Running",
    color: "var(--color-status-progress)",
    glow: "rgba(91, 141, 239, 0.08)",
  },
  {
    key: "completed",
    label: "Done",
    color: "var(--color-status-completed)",
    glow: "rgba(0, 255, 157, 0.06)",
  },
  {
    key: "failed",
    label: "Failed",
    color: "var(--color-status-failed)",
    glow: "rgba(255, 77, 106, 0.08)",
  },
] as const;

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function TaskBoard({
  tasks,
  agents,
}: {
  tasks: Task[];
  agents: Agent[];
}) {
  const agentMap = new Map(agents.map((a) => [a.id, a]));
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  return (
    <>
    {selectedTask && (
      <TaskDetail
        task={selectedTask}
        agents={agents}
        onClose={() => setSelectedTask(null)}
      />
    )}
    <div className="panel">
      <div className="panel-header">
        <h2>Task Pipeline</h2>
        <span
          className="font-mono text-[10px] tabular-nums"
          style={{ color: "var(--color-text-3)" }}
        >
          {tasks.length} total
        </span>
      </div>

      <div
        className="grid grid-cols-4"
        style={{ minHeight: "280px" }}
      >
        {columns.map((col, colIdx) => {
          const colTasks = tasks.filter((t) => t.status === col.key);
          return (
            <div
              key={col.key}
              className="flex flex-col"
              style={{
                borderRight:
                  colIdx < 3 ? "1px solid var(--color-ink-border)" : "none",
              }}
            >
              {/* Column header */}
              <div
                className="px-3 py-2.5 flex items-center gap-2"
                style={{
                  borderBottom: "1px solid var(--color-ink-border)",
                  background: col.glow,
                }}
              >
                {/* Status indicator bar */}
                <div
                  className="w-0.5 h-3 flex-shrink-0"
                  style={{
                    background: col.color,
                    boxShadow: col.key === "in_progress"
                      ? `0 0 8px ${col.color}`
                      : "none",
                  }}
                />
                <span
                  className="font-mono text-[10px] font-semibold tracking-wider uppercase"
                  style={{ color: col.color }}
                >
                  {col.label}
                </span>
                <span
                  className="font-mono text-[10px] ml-auto tabular-nums"
                  style={{ color: "var(--color-text-3)" }}
                >
                  {colTasks.length}
                </span>
              </div>

              {/* Cards */}
              <div
                className="flex-1 p-2 space-y-1.5 overflow-y-auto"
                style={{ maxHeight: "380px" }}
              >
                {colTasks.map((task) => (
                  <div
                    key={task.id}
                    className="p-3 transition-all duration-150 cursor-pointer glow-hover"
                    onClick={() => setSelectedTask(task)}
                    style={{
                      background: "var(--color-ink-2)",
                      border: "1px solid var(--color-ink-border)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "var(--color-ink-3)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "var(--color-ink-2)";
                    }}
                  >
                    {/* Title */}
                    <div
                      className="font-mono text-[11px] font-medium leading-snug"
                      style={{ color: "var(--color-text-0)" }}
                    >
                      {task.title}
                    </div>

                    {/* Description */}
                    {task.description && (
                      <div
                        className="font-mono text-[10px] leading-relaxed mt-1.5 line-clamp-2"
                        style={{ color: "var(--color-text-2)" }}
                      >
                        {task.description}
                      </div>
                    )}

                    {/* Meta row */}
                    <div className="flex items-center justify-between mt-2.5">
                      <span
                        className="font-mono text-[9px] font-medium uppercase tracking-wider"
                        style={{ color: col.color }}
                      >
                        {agentMap.get(task.assignee_id)?.name ||
                          task.assignee_id.slice(0, 8)}
                      </span>
                      <span
                        className="font-mono text-[9px] tabular-nums"
                        style={{ color: "var(--color-text-3)" }}
                      >
                        {formatTime(task.created_at)}
                      </span>
                    </div>

                    {/* Result */}
                    {task.result && (
                      <div
                        className="mt-2 px-2 py-1.5 font-mono text-[10px] leading-relaxed"
                        style={{
                          background: "rgba(0, 255, 157, 0.05)",
                          borderLeft: "2px solid var(--color-phosphor)",
                          color: "var(--color-phosphor-dim)",
                        }}
                      >
                        {task.result}
                      </div>
                    )}
                  </div>
                ))}

                {colTasks.length === 0 && (
                  <div className="flex items-center justify-center h-full min-h-[120px]">
                    <span
                      className="font-mono text-[9px] tracking-widest uppercase"
                      style={{ color: "var(--color-text-3)" }}
                    >
                      empty
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
    </>
  );
}

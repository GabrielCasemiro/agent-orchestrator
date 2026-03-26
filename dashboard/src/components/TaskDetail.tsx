"use client";

import { useEffect, useState, useCallback } from "react";
import { Task, Agent, Activity, fetchTaskActivities } from "@/lib/api";

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

const statusStyle: Record<string, { color: string; label: string }> = {
  pending: { color: "var(--color-status-pending)", label: "QUEUED" },
  in_progress: { color: "var(--color-status-progress)", label: "RUNNING" },
  completed: { color: "var(--color-status-completed)", label: "DONE" },
  failed: { color: "var(--color-status-failed)", label: "FAILED" },
};

export default function TaskDetail({
  task,
  agents,
  onClose,
}: {
  task: Task;
  agents: Agent[];
  onClose: () => void;
}) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const agentMap = new Map(agents.map((a) => [a.id, a]));
  const name = (id: string) => agentMap.get(id)?.name || id.slice(0, 8);
  const st = statusStyle[task.status] || statusStyle.pending;

  const loadActivities = useCallback(async () => {
    try {
      const acts = await fetchTaskActivities(task.id);
      setActivities(acts);
    } catch {
      // ignore
    }
  }, [task.id]);

  useEffect(() => {
    loadActivities();
    const interval = setInterval(loadActivities, 3000);
    return () => clearInterval(interval);
  }, [loadActivities]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0, 0, 0, 0.7)", backdropFilter: "blur(4px)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl max-h-[80vh] flex flex-col"
        style={{
          background: "var(--color-ink-1)",
          border: "1px solid var(--color-ink-border-bright)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4 flex-shrink-0"
          style={{ borderBottom: "1px solid var(--color-ink-border)" }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="w-1 h-8 flex-shrink-0"
              style={{ background: st.color }}
            />
            <div className="min-w-0">
              <div
                className="font-mono text-xs font-semibold"
                style={{ color: "var(--color-text-0)" }}
              >
                {task.title}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className="font-mono text-[9px] font-bold tracking-widest uppercase px-1.5 py-0.5"
                  style={{ color: st.color, background: `${st.color}15` }}
                >
                  {st.label}
                </span>
                <span
                  className="font-mono text-[9px]"
                  style={{ color: "var(--color-text-3)" }}
                >
                  {task.id.slice(0, 8)}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="font-mono text-[10px] px-2 py-1 transition-colors"
            style={{
              color: "var(--color-text-3)",
              border: "1px solid var(--color-ink-border)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--color-text-0)";
              e.currentTarget.style.borderColor = "var(--color-ink-border-bright)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--color-text-3)";
              e.currentTarget.style.borderColor = "var(--color-ink-border)";
            }}
          >
            ESC
          </button>
        </div>

        {/* Meta */}
        <div
          className="px-5 py-3 flex-shrink-0 grid grid-cols-2 gap-3"
          style={{ borderBottom: "1px solid var(--color-ink-border)" }}
        >
          <div>
            <div
              className="font-mono text-[9px] tracking-widest uppercase mb-1"
              style={{ color: "var(--color-text-3)" }}
            >
              Assigned to
            </div>
            <div
              className="font-mono text-[11px] font-medium"
              style={{ color: "var(--color-text-0)" }}
            >
              {name(task.assignee_id)}
            </div>
          </div>
          <div>
            <div
              className="font-mono text-[9px] tracking-widest uppercase mb-1"
              style={{ color: "var(--color-text-3)" }}
            >
              Created by
            </div>
            <div
              className="font-mono text-[11px] font-medium"
              style={{ color: "var(--color-text-0)" }}
            >
              {name(task.creator_id)} at {formatTime(task.created_at)}
            </div>
          </div>
          {task.description && (
            <div className="col-span-2">
              <div
                className="font-mono text-[9px] tracking-widest uppercase mb-1"
                style={{ color: "var(--color-text-3)" }}
              >
                Description
              </div>
              <div
                className="font-mono text-[11px] leading-relaxed"
                style={{ color: "var(--color-text-1)" }}
              >
                {task.description}
              </div>
            </div>
          )}
          {task.result && (
            <div className="col-span-2">
              <div
                className="font-mono text-[9px] tracking-widest uppercase mb-1"
                style={{ color: "var(--color-text-3)" }}
              >
                Result
              </div>
              <div
                className="font-mono text-[11px] leading-relaxed px-2 py-1.5"
                style={{
                  color: "var(--color-phosphor-dim)",
                  background: "rgba(0, 255, 157, 0.05)",
                  borderLeft: "2px solid var(--color-phosphor)",
                }}
              >
                {task.result}
              </div>
            </div>
          )}
        </div>

        {/* Activity log */}
        <div className="flex-1 overflow-y-auto min-h-0">
          <div
            className="px-5 py-2 sticky top-0 flex-shrink-0"
            style={{
              background: "var(--color-ink-2)",
              borderBottom: "1px solid var(--color-ink-border)",
            }}
          >
            <span
              className="font-mono text-[9px] tracking-widest uppercase"
              style={{ color: "var(--color-text-3)" }}
            >
              Activity Log ({activities.length})
            </span>
          </div>

          {activities.length === 0 && (
            <div className="px-5 py-8 text-center">
              <span
                className="font-mono text-[10px]"
                style={{ color: "var(--color-text-3)" }}
              >
                No activity logged yet
              </span>
            </div>
          )}

          <div className="px-5 py-2 space-y-0">
            {activities.map((act, i) => (
              <div
                key={act.id}
                className="flex gap-3 py-1.5"
                style={{
                  borderBottom:
                    i < activities.length - 1
                      ? "1px solid var(--color-ink-border)"
                      : "none",
                }}
              >
                <span
                  className="font-mono text-[10px] tabular-nums flex-shrink-0 w-14"
                  style={{ color: "var(--color-text-3)" }}
                >
                  {formatTime(act.timestamp)}
                </span>
                <span
                  className="font-mono text-[10px] font-semibold flex-shrink-0 w-20 truncate"
                  style={{ color: "var(--color-role-generalist)" }}
                >
                  {name(act.agent_id)}
                </span>
                <span
                  className="font-mono text-[10px] leading-relaxed"
                  style={{ color: "var(--color-text-1)" }}
                >
                  {act.content}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

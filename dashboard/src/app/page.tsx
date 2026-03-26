"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchAgents, fetchMessages, fetchTasks, fetchExport } from "@/lib/api";
import { useWebSocket, WSEvent } from "@/hooks/useWebSocket";
import AgentList from "@/components/AgentList";
import MessageFeed from "@/components/MessageFeed";
import TaskBoard from "@/components/TaskBoard";
import type { Agent, Message, Task } from "@/lib/api";

export default function Home() {
  const [project, setProject] = useState("default");
  const [projectInput, setProjectInput] = useState("default");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);

  const { connected, subscribe } = useWebSocket(project);

  const refresh = useCallback(async () => {
    try {
      const [a, m, t] = await Promise.all([
        fetchAgents(project),
        fetchMessages(project),
        fetchTasks(project),
      ]);
      setAgents(a);
      setMessages(m);
      setTasks(t);
    } catch {
      // API not available yet
    }
  }, [project]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    return subscribe((_event: WSEvent) => {
      refresh();
    });
  }, [subscribe, refresh]);

  return (
    <div className="min-h-screen flex flex-col animate-fade-in">
      {/* ── Top bar ──────────────────────────────── */}
      <header
        className="flex-shrink-0"
        style={{
          background: "var(--color-ink-1)",
          borderBottom: "1px solid var(--color-ink-border)",
        }}
      >
        <div className="max-w-[1400px] mx-auto px-5 py-3 flex items-center justify-between">
          {/* Logo + title */}
          <div className="flex items-center gap-3">
            {/* Logo mark — layered squares */}
            <div className="relative w-7 h-7">
              <div
                className="absolute inset-0"
                style={{
                  border: "1.5px solid var(--color-phosphor)",
                  opacity: 0.3,
                }}
              />
              <div
                className="absolute top-1 left-1 w-5 h-5"
                style={{
                  background: "var(--color-phosphor)",
                  opacity: 0.12,
                }}
              />
              <div
                className="absolute top-1.5 left-1.5 w-2 h-2"
                style={{
                  background: "var(--color-phosphor)",
                  boxShadow: "0 0 8px var(--color-phosphor)",
                }}
              />
            </div>

            <div>
              <h1
                className="text-[13px] font-semibold tracking-tight leading-none"
                style={{
                  fontFamily: "var(--font-display)",
                  color: "var(--color-text-0)",
                }}
              >
                Orchestrator
              </h1>
              <span
                className="font-mono text-[9px] tracking-widest uppercase"
                style={{ color: "var(--color-text-3)" }}
              >
                multi-agent control
              </span>
            </div>
          </div>

          {/* Right side controls */}
          <div className="flex items-center gap-5">
            {/* Project selector */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setProject(projectInput);
              }}
              className="flex items-center gap-2"
            >
              <label
                className="font-mono text-[9px] tracking-widest uppercase"
                style={{ color: "var(--color-text-3)" }}
              >
                Project
              </label>
              <div className="flex items-center">
                <input
                  type="text"
                  value={projectInput}
                  onChange={(e) => setProjectInput(e.target.value)}
                  className="font-mono text-[11px] w-28 px-2 py-1 outline-none"
                  style={{
                    background: "var(--color-ink-2)",
                    border: "1px solid var(--color-ink-border)",
                    color: "var(--color-text-0)",
                    caretColor: "var(--color-phosphor)",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-ink-border-bright)";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "var(--color-ink-border)";
                  }}
                />
                <button
                  type="submit"
                  className="font-mono text-[9px] font-semibold tracking-wider uppercase px-2 py-1 transition-colors duration-100"
                  style={{
                    background: "var(--color-ink-3)",
                    border: "1px solid var(--color-ink-border)",
                    borderLeft: "none",
                    color: "var(--color-text-2)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "var(--color-ink-4)";
                    e.currentTarget.style.color = "var(--color-text-0)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "var(--color-ink-3)";
                    e.currentTarget.style.color = "var(--color-text-2)";
                  }}
                >
                  Go
                </button>
              </div>
            </form>

            {/* Divider */}
            <div
              className="w-px h-4"
              style={{ background: "var(--color-ink-border)" }}
            />

            {/* Export button */}
            <button
              onClick={async () => {
                try {
                  const md = await fetchExport(project);
                  await navigator.clipboard.writeText(md);
                  alert("Exported to clipboard!");
                } catch {
                  alert("Export failed");
                }
              }}
              className="font-mono text-[9px] font-semibold tracking-wider uppercase px-2 py-1 transition-colors duration-100"
              style={{
                background: "var(--color-ink-3)",
                border: "1px solid var(--color-ink-border)",
                color: "var(--color-text-2)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--color-ink-4)";
                e.currentTarget.style.color = "var(--color-phosphor-dim)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "var(--color-ink-3)";
                e.currentTarget.style.color = "var(--color-text-2)";
              }}
            >
              Export
            </button>

            {/* Divider */}
            <div
              className="w-px h-4"
              style={{ background: "var(--color-ink-border)" }}
            />

            {/* Connection status */}
            <div className="flex items-center gap-2">
              <div
                className={`w-1.5 h-1.5 ${connected ? "animate-pulse-glow" : ""}`}
                style={{
                  background: connected
                    ? "var(--color-phosphor)"
                    : "var(--color-status-failed)",
                  boxShadow: connected
                    ? "0 0 6px var(--color-phosphor)"
                    : "none",
                }}
              />
              <span
                className="font-mono text-[10px] uppercase tracking-wider"
                style={{
                  color: connected
                    ? "var(--color-phosphor-dim)"
                    : "var(--color-status-failed)",
                }}
              >
                {connected ? "live" : "offline"}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* ── Main grid ────────────────────────────── */}
      <main className="flex-1 max-w-[1400px] mx-auto w-full px-5 py-5 flex flex-col gap-4">
        {/* Top row: agents + messages */}
        <div className="grid grid-cols-12 gap-4 flex-1 min-h-0">
          <div className="col-span-3">
            <AgentList agents={agents} />
          </div>
          <div className="col-span-9">
            <MessageFeed messages={messages} agents={agents} />
          </div>
        </div>

        {/* Bottom: task pipeline */}
        <TaskBoard tasks={tasks} agents={agents} />
      </main>

      {/* ── Footer accent line ───────────────────── */}
      <div
        className="h-px flex-shrink-0"
        style={{
          background:
            "linear-gradient(90deg, transparent 5%, var(--color-phosphor) 50%, transparent 95%)",
          opacity: 0.15,
        }}
      />
    </div>
  );
}

"use client";

import { Agent } from "@/lib/api";

const roleConfig: Record<string, { color: string; glow: string; label: string }> = {
  backend: {
    color: "var(--color-role-backend)",
    glow: "rgba(91, 141, 239, 0.15)",
    label: "SYS",
  },
  frontend: {
    color: "var(--color-role-frontend)",
    glow: "rgba(192, 132, 252, 0.15)",
    label: "UI",
  },
  devops: {
    color: "var(--color-role-devops)",
    glow: "rgba(245, 158, 11, 0.15)",
    label: "OPS",
  },
  generalist: {
    color: "var(--color-role-generalist)",
    glow: "rgba(52, 211, 153, 0.15)",
    label: "GEN",
  },
};

function getRole(role: string) {
  return roleConfig[role.toLowerCase()] || roleConfig.generalist;
}

export default function AgentList({ agents }: { agents: Agent[] }) {
  return (
    <div className="panel h-full">
      <div className="panel-header">
        <h2>Agents</h2>
        <div className="flex items-center gap-2">
          <span
            className="font-mono text-[10px] tabular-nums"
            style={{ color: "var(--color-phosphor)" }}
          >
            {agents.filter((a) => a.status === "online").length}
          </span>
          <span className="font-mono text-[10px]" style={{ color: "var(--color-text-3)" }}>
            /{agents.length}
          </span>
        </div>
      </div>

      <div className="stagger-children">
        {agents.length === 0 && (
          <div className="px-4 py-12 text-center">
            <div
              className="font-mono text-[10px] tracking-widest uppercase"
              style={{ color: "var(--color-text-3)" }}
            >
              Awaiting connections
            </div>
            <div className="mt-2 flex justify-center gap-1">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-1 h-1 rounded-full animate-pulse-glow"
                  style={{
                    background: "var(--color-phosphor)",
                    animationDelay: `${i * 0.3}s`,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {agents.map((agent) => {
          const role = getRole(agent.role);
          return (
            <div
              key={agent.id}
              className="group flex items-center gap-3 px-4 py-3 transition-colors duration-150 cursor-default"
              style={{
                borderBottom: "1px solid var(--color-ink-border)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--color-ink-2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              {/* Status indicator + avatar */}
              <div className="relative flex-shrink-0">
                <div
                  className="w-8 h-8 flex items-center justify-center font-mono text-[10px] font-bold uppercase tracking-wider"
                  style={{
                    background: role.glow,
                    color: role.color,
                    border: `1px solid ${role.color}33`,
                  }}
                >
                  {agent.name.slice(0, 2)}
                </div>
                {/* Status dot */}
                <div
                  className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 ${agent.status === "online" ? "animate-pulse-glow" : ""}`}
                  style={{
                    background: agent.status === "online" ? "var(--color-phosphor)" : "var(--color-text-3)",
                    borderRadius: "1px",
                    boxShadow: agent.status === "online" ? "0 0 6px var(--color-phosphor)" : "none",
                  }}
                />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div
                  className="font-mono text-xs font-medium truncate"
                  style={{ color: "var(--color-text-0)" }}
                >
                  {agent.name}
                </div>
                <div
                  className="font-mono text-[10px] truncate mt-0.5"
                  style={{ color: "var(--color-text-3)" }}
                >
                  {agent.id.slice(0, 8)}...
                </div>
              </div>

              {/* Role badge */}
              <div
                className="flex-shrink-0 px-1.5 py-0.5 font-mono text-[9px] font-semibold tracking-widest uppercase"
                style={{
                  color: role.color,
                  background: role.glow,
                  border: `1px solid ${role.color}22`,
                }}
              >
                {role.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

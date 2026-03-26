"use client";

import { useRef, useEffect } from "react";
import { Message, Agent } from "@/lib/api";

const senderPalette = [
  { color: "#5b8def", dim: "rgba(91, 141, 239, 0.08)" },
  { color: "#c084fc", dim: "rgba(192, 132, 252, 0.08)" },
  { color: "#f59e0b", dim: "rgba(245, 158, 11, 0.08)" },
  { color: "#34d399", dim: "rgba(52, 211, 153, 0.08)" },
  { color: "#ff4d6a", dim: "rgba(255, 77, 106, 0.08)" },
  { color: "#06b6d4", dim: "rgba(6, 182, 212, 0.08)" },
];

function hashColor(id: string) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
  return senderPalette[Math.abs(h) % senderPalette.length];
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export default function MessageFeed({
  messages,
  agents,
}: {
  messages: Message[];
  agents: Agent[];
}) {
  const agentMap = new Map(agents.map((a) => [a.id, a]));
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  return (
    <div className="panel h-full flex flex-col">
      <div className="panel-header">
        <h2>Message Feed</h2>
        <span
          className="font-mono text-[10px] tabular-nums"
          style={{ color: "var(--color-text-3)" }}
        >
          {messages.length} msg
        </span>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto min-h-0"
        style={{ maxHeight: "500px" }}
      >
        {messages.length === 0 && (
          <div className="px-4 py-16 text-center">
            <div
              className="font-mono text-[10px] tracking-widest uppercase"
              style={{ color: "var(--color-text-3)" }}
            >
              No transmissions
            </div>
          </div>
        )}

        <div className="stagger-children">
          {messages.map((msg) => {
            const sender = agentMap.get(msg.sender_id);
            const senderName = sender?.name || msg.sender_id.slice(0, 8);
            const palette = hashColor(msg.sender_id);
            const isStatus = msg.content.startsWith("[STATUS]");

            return (
              <div
                key={msg.id}
                className="group px-4 py-2 transition-colors duration-100"
                style={{ borderBottom: "1px solid var(--color-ink-border)" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = palette.dim;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <div className="flex items-baseline gap-0">
                  {/* Timestamp */}
                  <span
                    className="font-mono text-[10px] tabular-nums flex-shrink-0 w-16"
                    style={{ color: "var(--color-text-3)" }}
                  >
                    {formatTime(msg.timestamp)}
                  </span>

                  {/* Sender */}
                  <span
                    className="font-mono text-[11px] font-semibold flex-shrink-0"
                    style={{ color: palette.color }}
                  >
                    {senderName}
                  </span>

                  {/* Arrow + recipient */}
                  {msg.recipient_id && (
                    <span className="flex items-center gap-1 ml-1 flex-shrink-0">
                      <span
                        className="font-mono text-[10px]"
                        style={{ color: "var(--color-text-3)" }}
                      >
                        {"\u2192"}
                      </span>
                      <span
                        className="font-mono text-[11px] font-medium"
                        style={{
                          color: hashColor(msg.recipient_id).color,
                        }}
                      >
                        {agentMap.get(msg.recipient_id)?.name ||
                          msg.recipient_id.slice(0, 8)}
                      </span>
                    </span>
                  )}

                  {/* Separator */}
                  <span
                    className="font-mono text-[10px] mx-2 flex-shrink-0"
                    style={{ color: "var(--color-text-3)" }}
                  >
                    {"\u2502"}
                  </span>

                  {/* Content */}
                  <span
                    className={`font-mono text-[11px] leading-relaxed break-words min-w-0 ${
                      isStatus ? "italic" : ""
                    }`}
                    style={{
                      color: isStatus
                        ? "var(--color-text-2)"
                        : "var(--color-text-1)",
                    }}
                  >
                    {msg.content}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom edge glow */}
      <div
        className="h-px flex-shrink-0"
        style={{
          background:
            "linear-gradient(90deg, transparent, var(--color-ink-border-bright), transparent)",
        }}
      />
    </div>
  );
}

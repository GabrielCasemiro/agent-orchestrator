"use client";

import { useEffect, useRef, useCallback, useState } from "react";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export interface WSEvent {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket(project: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const listenersRef = useRef<Set<(event: WSEvent) => void>>(new Set());

  const subscribe = useCallback((listener: (event: WSEvent) => void) => {
    listenersRef.current.add(listener);
    return () => {
      listenersRef.current.delete(listener);
    };
  }, []);

  useEffect(() => {
    if (!project) return;

    let ws: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(`${WS_BASE}/ws/${encodeURIComponent(project)}`);

      ws.onopen = () => setConnected(true);

      ws.onmessage = (event) => {
        try {
          const data: WSEvent = JSON.parse(event.data);
          setLastEvent(data);
          listenersRef.current.forEach((fn) => fn(data));
        } catch {
          // ignore non-JSON messages
        }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();

      wsRef.current = ws;
    }

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [project]);

  return { lastEvent, connected, subscribe };
}

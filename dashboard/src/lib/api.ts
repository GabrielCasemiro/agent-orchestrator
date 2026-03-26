const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Agent {
  id: string;
  name: string;
  role: string;
  project: string;
  status: string;
  last_heartbeat: string;
}

export interface Message {
  id: string;
  sender_id: string;
  project: string;
  content: string;
  recipient_id: string | null;
  timestamp: string;
}

export interface Task {
  id: string;
  project: string;
  creator_id: string;
  assignee_id: string;
  title: string;
  description: string;
  status: string;
  result: string;
  created_at: string;
  updated_at: string;
}

export async function fetchAgents(project: string): Promise<Agent[]> {
  const res = await fetch(`${API_BASE}/api/v1/agents?project=${encodeURIComponent(project)}`);
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function fetchMessages(project: string, limit = 50): Promise<Message[]> {
  const res = await fetch(
    `${API_BASE}/api/v1/messages?project=${encodeURIComponent(project)}&limit=${limit}`
  );
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}

export interface Activity {
  id: string;
  agent_id: string;
  project: string;
  task_id: string | null;
  content: string;
  timestamp: string;
}

export async function fetchTasks(project: string): Promise<Task[]> {
  const res = await fetch(`${API_BASE}/api/v1/tasks?project=${encodeURIComponent(project)}`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function fetchTaskActivities(taskId: string): Promise<Activity[]> {
  const res = await fetch(`${API_BASE}/api/v1/tasks/${encodeURIComponent(taskId)}/activities`);
  if (!res.ok) throw new Error("Failed to fetch activities");
  return res.json();
}

export async function fetchExport(project: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/export?project=${encodeURIComponent(project)}`);
  if (!res.ok) throw new Error("Failed to export");
  return res.text();
}

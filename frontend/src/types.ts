export type AppMode = "idle" | "chat" | "dashboard";

export type OrbActivity =
  | "idle"
  | "thinking"
  | "tool"
  | "streaming"
  | "error"
  | "disconnected";

export interface ToolEvent {
  id: string;
  tool: string;
  timestamp: number;
  status: "executing" | "done";
}

export interface ResponseBlock {
  id: string;
  type: "text" | "screenshot";
  content: string;
  timestamp: number;
}

export interface MonitorInfo {
  id: number;
  width: number;
  height: number;
  left: number;
  top: number;
}

export interface MonitorSelectRequest {
  monitors: MonitorInfo[];
  requestId: string;
}

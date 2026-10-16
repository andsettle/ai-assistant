import { useRef, useCallback, useEffect } from "react";

interface WebSocketCallbacks {
  onConnect: () => void;
  onDisconnect: () => void;
  onReconnecting: () => void;
  onThinking: () => void;
  onToolExecution: (tool: string) => void;
  onToolResult: (data: { tool: string; image_base64?: string }) => void;
  onChunk: (text: string) => void;
  onDone: () => void;
  onMonitorSelect: (data: { monitors: { id: number; width: number; height: number; left: number; top: number }[]; request_id: string }) => void;
  onSuggestion?: (content: string) => void;
}

export function useWebSocket(callbacks: WebSocketCallbacks) {
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef("");
  const reconnectDelayRef = useRef(1000);
  const intentionalCloseRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbacksRef = useRef(callbacks);
  callbacksRef.current = callbacks;

  const connect = useCallback(() => {
    // Reset intentional close flag — we're actively trying to connect
    intentionalCloseRef.current = false;

    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {
        /* ignore */
      }
    }

    const ws = new WebSocket("ws://localhost:8000/ws/chat");

    ws.onopen = () => {
      reconnectDelayRef.current = 1000;
      callbacksRef.current.onConnect();
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "session":
          sessionIdRef.current = data.session_id;
          break;
        case "status":
          if (data.status === "thinking") callbacksRef.current.onThinking();
          break;
        case "tool_execution":
          callbacksRef.current.onToolExecution(data.tool);
          break;
        case "tool_result":
          callbacksRef.current.onToolResult(data);
          break;
        case "chunk":
          callbacksRef.current.onChunk(data.content);
          break;
        case "done":
          callbacksRef.current.onDone();
          break;
        case "monitor_select":
          callbacksRef.current.onMonitorSelect(data);
          break;
        case "suggestion":
          if (callbacksRef.current.onSuggestion) {
            callbacksRef.current.onSuggestion(data.content);
          }
          break;
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
      callbacksRef.current.onDisconnect();
      if (!intentionalCloseRef.current) {
        callbacksRef.current.onReconnecting();
        const delay = reconnectDelayRef.current;
        reconnectTimerRef.current = setTimeout(() => {
          reconnectDelayRef.current = Math.min(delay * 2, 30000);
          connect();
        }, delay);
      }
    };

    ws.onerror = () => {
      // onclose will fire after this
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      intentionalCloseRef.current = true;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const getSessionId = useCallback(() => sessionIdRef.current, []);

  return { send, getSessionId };
}

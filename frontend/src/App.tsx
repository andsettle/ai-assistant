import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { getCurrentWindow } from "@tauri-apps/api/window";
import type { AppMode, OrbActivity, ToolEvent, ResponseBlock, MonitorInfo } from "./types";
import { useWebSocket } from "./hooks/useWebSocket";
import { useWindowManager } from "./hooks/useWindowManager";
import { Robot } from "./components/Robot";
import { ContextRibbon } from "./components/ContextRibbon";
import { MonitorSelector } from "./components/MonitorSelector";
import "./App.css";

const TRUNCATE_LENGTH = 280;

function ChatMessageText({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const needsTruncation = text.length > TRUNCATE_LENGTH;

  if (!needsTruncation || expanded) {
    return (
      <div className="chat-message-text">
        {text}
        {expanded && (
          <button className="see-more-btn" onClick={() => setExpanded(false)}>
            show less
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="chat-message-text">
      {text.slice(0, TRUNCATE_LENGTH).trimEnd()}&hellip;{" "}
      <button className="see-more-btn" onClick={() => setExpanded(true)}>
        see more
      </button>
    </div>
  );
}

function App() {
  const [mode, setMode] = useState<AppMode>("idle");
  const [activity, setActivity] = useState<OrbActivity>("disconnected");
  const [isConnected, setIsConnected] = useState(false);
  const [input, setInput] = useState("");
  const [currentResponse, setCurrentResponse] = useState("");
  const [responses, setResponses] = useState<ResponseBlock[]>([]);
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [monitorSelectMonitors, setMonitorSelectMonitors] = useState<MonitorInfo[] | null>(null);
  const [suggestion, setSuggestion] = useState<string | null>(null);
  
  const monitorSelectRequestIdRef = useRef("");
  const currentResponseRef = useRef("");
  const activityRef = useRef<OrbActivity>("disconnected");
  const responseTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastClickTimeRef = useRef<number>(0);
  const chatOpenedAtRef = useRef<number>(0);
  const windowManager = useWindowManager();

  const RESPONSE_TIMEOUT_MS = 90_000;

  useEffect(() => {
    windowManager.setModeSize("idle");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (mode === "chat" && inputRef.current) {
      // Delay focus until after Tauri window resize settles + Framer Motion animation starts
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [mode]);

  const clearResponseTimeout = () => {
    if (responseTimeoutRef.current) {
      clearTimeout(responseTimeoutRef.current);
      responseTimeoutRef.current = null;
    }
  };

  const startResponseTimeout = () => {
    clearResponseTimeout();
    responseTimeoutRef.current = setTimeout(() => {
      const act = activityRef.current;
      if (act === "thinking" || act === "tool" || act === "streaming") {
        const partial = currentResponseRef.current.trim();
        const timeoutMsg = partial
          ? partial + "\n\n[Response timed out]"
          : "[Response timed out — the model may be overloaded. Try again.]";
        setResponses((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            type: "text",
            content: timeoutMsg,
            timestamp: Date.now(),
          },
        ]);
        currentResponseRef.current = "";
        setCurrentResponse("");
        setActivity("idle");
        activityRef.current = "idle";
      }
    }, RESPONSE_TIMEOUT_MS);
  };

  const ws = useWebSocket({
    onConnect: () => {
      setIsConnected(true);
      setActivity("idle");
      activityRef.current = "idle";
    },
    onDisconnect: () => {
      clearResponseTimeout();
      setIsConnected(false);
      setActivity("disconnected");
      activityRef.current = "disconnected";
    },
    onReconnecting: () => {
      setActivity("disconnected");
      activityRef.current = "disconnected";
    },
    onThinking: () => {
      setActivity("thinking");
      activityRef.current = "thinking";
    },
    onToolExecution: (tool: string) => {
      setActivity("tool");
      activityRef.current = "tool";
      const id = crypto.randomUUID();
      setToolEvents((prev) => [
        ...prev,
        { id, tool, timestamp: Date.now(), status: "executing" },
      ]);
      setTimeout(() => {
        setToolEvents((prev) => prev.filter((e) => e.id !== id));
      }, 8000);
    },
    onToolResult: (data) => {
      setToolEvents((prev) =>
        prev.map((e) =>
          e.status === "executing" ? { ...e, status: "done" as const } : e
        )
      );
      if (data.tool === "capture_screen" && data.image_base64) {
        setResponses((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            type: "screenshot",
            content: data.image_base64!,
            timestamp: Date.now(),
          },
        ]);
      }
    },
    onChunk: (text: string) => {
      if (activityRef.current !== "streaming") {
        setActivity("streaming");
        activityRef.current = "streaming";
      }
      currentResponseRef.current += text;
      setCurrentResponse(currentResponseRef.current);
    },
    onMonitorSelect: (data) => {
      setMonitorSelectMonitors(data.monitors);
      monitorSelectRequestIdRef.current = data.request_id;
    },
    onSuggestion: (content: string) => {
      setSuggestion(content);
    },
    onDone: () => {
      clearResponseTimeout();
      const finalText = currentResponseRef.current.trim();
      if (finalText) {
        setResponses((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            type: "text",
            content: finalText,
            timestamp: Date.now(),
          },
        ]);
      }
      currentResponseRef.current = "";
      setCurrentResponse("");
      setActivity("idle");
      activityRef.current = "idle";
    },
  });

  const handleMonitorSelect = useCallback((monitorId: number) => {
    ws.send({
      type: "monitor_select_response",
      monitor: monitorId,
      request_id: monitorSelectRequestIdRef.current,
    });
    setMonitorSelectMonitors(null);
  }, [ws]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !isConnected) return;
    
    setResponses([]);
    setSuggestion(null);
    
    ws.send({
      type: "message",
      message: input,
      session_id: ws.getSessionId(),
      is_sensitive: false,
    });
    setInput("");
    startResponseTimeout();
  }, [input, isConnected, ws]);

  const switchToChat = useCallback(async () => {
    if (mode === "idle") {
      chatOpenedAtRef.current = Date.now();
      setMode("chat");
      await windowManager.setModeSize("chat");
    }
  }, [mode, windowManager]);

  const switchToDashboard = useCallback(async () => {
    setMode("dashboard");
    await windowManager.setModeSize("dashboard");
  }, [windowManager]);

  const handleShrinkToIdle = useCallback(async () => {
    // Don't collapse during the first 500ms after opening chat (window resize can cause spurious blur/leave)
    if (Date.now() - chatOpenedAtRef.current < 500) return;
    // Shrink as long as Navi isn't actively processing or typing
    if (activity !== "thinking" && activity !== "streaming" && activity !== "tool") {
      setMode("idle");
      await windowManager.setModeSize("idle");
    }
  }, [activity, windowManager]);

  const shrinkToIdleRef = useRef(handleShrinkToIdle);
  shrinkToIdleRef.current = handleShrinkToIdle;

  const handleRobotClick = useCallback(async () => {
    const now = Date.now();
    if (now - lastClickTimeRef.current < 300) {
      // Double click
      await switchToDashboard();
    } else {
      // Single click
      if (mode === "idle") {
        await switchToChat();
        setTimeout(() => inputRef.current?.focus(), 300);
      } else if (mode === "chat" || mode === "dashboard") {
        setMode("idle");
        await windowManager.setModeSize("idle");
      }
    }
    lastClickTimeRef.current = now;
  }, [mode, switchToChat, switchToDashboard, windowManager]);

  const robotDragHandlers = useMemo(
    () => windowManager.makeDragHandlers(handleRobotClick),
    [windowManager, handleRobotClick]
  );

  // Auto-collapse to idle after the window has been unfocused for a sustained period.
  // This avoids premature collapse from transient focus loss (common on Windows with Tauri).
  const blurTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let unlisten: (() => void) | null = null;
    let isMounted = true;

    getCurrentWindow()
      .onFocusChanged(({ payload: focused }) => {
        if (!focused) {
          // Only collapse after 2 seconds of sustained focus loss
          blurTimerRef.current = setTimeout(() => {
            shrinkToIdleRef.current();
          }, 2000);
        } else {
          // Window regained focus — cancel the pending collapse
          if (blurTimerRef.current) {
            clearTimeout(blurTimerRef.current);
            blurTimerRef.current = null;
          }
        }
      })
      .then((fn) => {
        if (isMounted) unlisten = fn;
        else fn();
      });

    return () => {
      isMounted = false;
      if (blurTimerRef.current) clearTimeout(blurTimerRef.current);
      if (unlisten) unlisten();
    };
  }, []);

  return (
    <div
      className={`app-root ${mode}`}
    >
      {/* Robot stays permanently mounted outside AnimatePresence to avoid Canvas destruction */}
      <div className="robot-anchor">
        <Robot
          variant="full"
          activity={activity}
          onPointerDown={robotDragHandlers.onPointerDown}
          onPointerMove={robotDragHandlers.onPointerMove}
          onPointerUp={robotDragHandlers.onPointerUp}
        />
      </div>

      <AnimatePresence>
        {mode === "idle" && suggestion && (
          <motion.div 
            key="suggestion"
            className="suggestion-bubble"
            initial={{ opacity: 0, y: 10, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={(e) => {
              e.stopPropagation();
              setInput("Yes please! " + suggestion);
              switchToChat();
              setSuggestion(null);
            }}
          >
            <span className="suggestion-icon">💡</span> {suggestion}
          </motion.div>
        )}

        {mode === "chat" && (
          <motion.div
            key="chat-ui"
            className="chat-ui-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="chat-bubble-area">
              <AnimatePresence>
                {(responses.length > 0 || currentResponse) && (
                  <motion.div
                    className="chat-bubble"
                    initial={{ opacity: 0, y: 10, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                  >
                    <div className="chat-content">
                      {responses.map((res) => (
                        <div key={res.id} className="chat-message">
                          {res.type === "text"
                            ? <ChatMessageText text={res.content} />
                            : <img src={`data:image/jpeg;base64,${res.content}`} alt="Screenshot" className="chat-screenshot" />}
                        </div>
                      ))}
                      {currentResponse && (
                        <div className="chat-message current-streaming">
                          {currentResponse}<span className="cursor-blink">_</span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="chat-spacer-for-robot">
              <div className="chat-ribbon-container">
                <ContextRibbon events={toolEvents} />
              </div>
            </div>

            <div className="chat-input-wrapper">
              <input
                ref={inputRef}
                autoFocus
                type="text"
                className="command-input"
                placeholder="Ask Navi..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSend();
                }}
                disabled={!isConnected}
              />
            </div>
          </motion.div>
        )}

        {mode === "dashboard" && (
          <motion.div
            key="dashboard"
            className="dashboard-container"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <div className="dashboard-sidebar">
              <h3>Navi Settings</h3>
              <ul>
                <li>Chat History</li>
                <li>System Monitor</li>
                <li>Memory Settings</li>
              </ul>
              <button onClick={() => { setMode("idle"); windowManager.setModeSize("idle"); }} className="dashboard-close-btn">
                Close
              </button>
            </div>
            <div className="dashboard-main">
              <div className="dashboard-placeholder">
                <h2>Dashboard Placeholder</h2>
                <p>Advanced feature-rich interface goes here.</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {monitorSelectMonitors && mode === "chat" && (
        <div className="chat-ui-overlay" style={{ pointerEvents: 'auto', zIndex: 10 }}>
          <MonitorSelector
            monitors={monitorSelectMonitors}
            onSelect={handleMonitorSelect}
          />
        </div>
      )}
    </div>
  );
}

export default App;

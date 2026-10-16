import { motion } from "framer-motion";
import type { OrbActivity, ToolEvent, ResponseBlock, MonitorInfo } from "../types";
import { Robot } from "./Robot";
import { CommandInput } from "./CommandInput";
import { ResponseArea } from "./ResponseArea";
import { ContextRibbon } from "./ContextRibbon";
import { MonitorSelector } from "./MonitorSelector";

interface ExpandedPanelProps {
  activity: OrbActivity;
  isConnected: boolean;
  responses: ResponseBlock[];
  currentResponse: string;
  toolEvents: ToolEvent[];
  input: string;
  onInputChange: (val: string) => void;
  onSend: () => void;
  headerDragHandlers: {
    onPointerDown: (e: React.PointerEvent) => void;
    onPointerMove: (e: React.PointerEvent) => void;
    onPointerUp: (e: React.PointerEvent) => void;
  };
  miniOrbDragHandlers: {
    onPointerDown: (e: React.PointerEvent) => void;
    onPointerMove: (e: React.PointerEvent) => void;
    onPointerUp: (e: React.PointerEvent) => void;
  };
  monitorSelectMonitors: MonitorInfo[] | null;
  onMonitorSelect: (monitorId: number) => void;
}

const panelVariants = {
  collapsed: {
    opacity: 0,
    scale: 0.8,
    y: 20,
    transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] as const },
  },
  expanded: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0, 0, 0.2, 1] as const,
      staggerChildren: 0.08,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.85,
    y: 10,
    transition: { duration: 0.25, ease: [0.4, 0, 1, 1] as const },
  },
};

export function ExpandedPanel({
  activity,
  isConnected,
  responses,
  currentResponse,
  toolEvents,
  input,
  onInputChange,
  onSend,
  headerDragHandlers,
  miniOrbDragHandlers,
  monitorSelectMonitors,
  onMonitorSelect,
}: ExpandedPanelProps) {
  return (
    <motion.div
      className="expanded-panel"
      variants={panelVariants}
      initial="collapsed"
      animate="expanded"
      exit="exit"
    >
      <div
        className="panel-header"
        onPointerDown={headerDragHandlers.onPointerDown}
        onPointerMove={headerDragHandlers.onPointerMove}
        onPointerUp={headerDragHandlers.onPointerUp}
      >
        <Robot
          variant="mini"
          activity={activity}
          onPointerDown={(e) => {
            e.stopPropagation();
            miniOrbDragHandlers.onPointerDown(e);
          }}
          onPointerMove={(e) => {
            e.stopPropagation();
            miniOrbDragHandlers.onPointerMove(e);
          }}
          onPointerUp={(e) => {
            e.stopPropagation();
            miniOrbDragHandlers.onPointerUp(e);
          }}
        />
        <div className="panel-header-status">
          {!isConnected && (
            <span className="connection-status">reconnecting</span>
          )}
        </div>
      </div>

      <ContextRibbon events={toolEvents} />

      <CommandInput
        value={input}
        onChange={onInputChange}
        onSubmit={onSend}
        disabled={!isConnected}
        placeholder={isConnected ? "Ask anything..." : "Connecting..."}
      />

      <ResponseArea
        responses={responses}
        currentResponse={currentResponse}
        isStreaming={activity === "streaming"}
      />

      {monitorSelectMonitors && (
        <MonitorSelector
          monitors={monitorSelectMonitors}
          onSelect={onMonitorSelect}
        />
      )}
    </motion.div>
  );
}

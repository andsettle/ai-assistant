import { motion, AnimatePresence } from "framer-motion";
import type { ToolEvent } from "../types";

interface ContextRibbonProps {
  events: ToolEvent[];
}

const TOOL_LABELS: Record<string, string> = {
  list_files: "listing files",
  read_file: "reading file",
  write_file: "writing file",
  capture_screen: "capturing screen",
  get_system_info: "checking system",
  search_files: "searching files",
};

const pillVariants = {
  initial: { opacity: 0, scale: 0.7, x: -10 },
  animate: {
    opacity: 1,
    scale: 1,
    x: 0,
    transition: { type: "spring" as const, stiffness: 500, damping: 30 },
  },
  exit: {
    opacity: 0,
    scale: 0.8,
    x: 10,
    transition: { duration: 0.3 },
  },
};

export function ContextRibbon({ events }: ContextRibbonProps) {
  if (events.length === 0) return null;

  return (
    <div className="context-ribbon">
      <AnimatePresence mode="popLayout">
        {events.map((evt) => (
          <motion.span
            key={evt.id}
            className={`tool-pill ${evt.status}`}
            variants={pillVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            layout
          >
            <span className="tool-pill-dot" />
            <span className="tool-pill-label">
              {TOOL_LABELS[evt.tool] || evt.tool.replace(/_/g, " ")}
            </span>
          </motion.span>
        ))}
      </AnimatePresence>
    </div>
  );
}

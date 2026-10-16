import { motion, AnimatePresence } from "framer-motion";
import type { MonitorInfo } from "../types";

interface MonitorSelectorProps {
  monitors: MonitorInfo[];
  onSelect: (monitorId: number) => void;
}

export function MonitorSelector({ monitors, onSelect }: MonitorSelectorProps) {
  // Compute bounding box of all monitors to normalize positions
  const minLeft = Math.min(...monitors.map((m) => m.left));
  const minTop = Math.min(...monitors.map((m) => m.top));
  const maxRight = Math.max(...monitors.map((m) => m.left + m.width));
  const maxBottom = Math.max(...monitors.map((m) => m.top + m.height));
  const totalW = maxRight - minLeft;
  const totalH = maxBottom - minTop;

  // Scale to fit inside a container (~360px wide, maintain aspect ratio)
  const containerW = 360;
  const scale = containerW / totalW;
  const containerH = totalH * scale;

  return (
    <AnimatePresence>
      <motion.div
        className="monitor-selector-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        <div className="monitor-selector-content">
          <div className="monitor-selector-title">Select a display</div>

          <div
            className="monitor-selector-layout"
            style={{ width: containerW, height: containerH }}
          >
            {monitors.map((mon) => {
              const x = (mon.left - minLeft) * scale;
              const y = (mon.top - minTop) * scale;
              const w = mon.width * scale;
              const h = mon.height * scale;

              return (
                <motion.button
                  key={mon.id}
                  className="monitor-selector-item"
                  style={{
                    left: x,
                    top: y,
                    width: w,
                    height: h,
                  }}
                  onClick={() => onSelect(mon.id)}
                  whileHover={{ scale: 1.03, borderColor: "rgba(109, 211, 255, 0.8)" }}
                  whileTap={{ scale: 0.98 }}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: mon.id * 0.08 }}
                >
                  <span className="monitor-selector-number">{mon.id}</span>
                  <span className="monitor-selector-res">
                    {mon.width}&times;{mon.height}
                  </span>
                </motion.button>
              );
            })}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

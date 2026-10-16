import { useCallback, useMemo, useRef } from "react";
import { getCurrentWindow, LogicalSize, LogicalPosition } from "@tauri-apps/api/window";
import type { AppMode } from "../types";

const SIZES = {
  idle: { width: 160, height: 160, robotY: 80 },
  chat: { width: 400, height: 500, robotY: 349 }, // 500 - (20 pad + 46 input + 15 marg + 70 half-bot) = 349
  dashboard: { width: 800, height: 600, robotY: 300 }, // centered
};

const DRAG_THRESHOLD = 5; // pixels before mousedown becomes a drag

export function useWindowManager() {
  const currentModeRef = useRef<AppMode>("idle");
  const isResizingRef = useRef(false);

  const setModeSize = useCallback(async (newMode: AppMode) => {
    if (isResizingRef.current) return;
    isResizingRef.current = true;
    
    try {
      const win = getCurrentWindow();
      const pos = await win.outerPosition();
      
      const currentMode = currentModeRef.current;
      const targetSize = SIZES[newMode];
      const currentSize = SIZES[currentMode];

      // Calculate where the robot currently is on screen
      const oldRobotScreenX = pos.x + currentSize.width / 2;
      const oldRobotScreenY = pos.y + currentSize.robotY;

      // Position the new window so the robot stays at the exact same screen coordinates
      const newX = Math.max(0, Math.round(oldRobotScreenX - targetSize.width / 2));
      const newY = Math.max(0, Math.round(oldRobotScreenY - targetSize.robotY));

      currentModeRef.current = newMode;

      // We set size first, then position. Doing this quickly prevents severe visual jumping.
      await win.setSize(new LogicalSize(targetSize.width, targetSize.height));
      await win.setPosition(new LogicalPosition(newX, newY));
      
      // Ensure the OS window gains focus so the input field can be typed into immediately
      if (newMode === "chat" || newMode === "dashboard") {
        await win.setFocus();
      }
    } catch {
      // ignore
    } finally {
      // small delay to let OS catch up before allowing another resize
      setTimeout(() => {
        isResizingRef.current = false;
      }, 50);
    }
  }, []);

  const dragStartRef = useRef<{ x: number; y: number } | null>(null);
  const didDragRef = useRef(false);

  const makeDragHandlers = useCallback(
    (onClick: () => void) => {
      const onPointerDown = (e: React.PointerEvent) => {
        if (e.button !== 0) return;
        dragStartRef.current = { x: e.clientX, y: e.clientY };
        didDragRef.current = false;
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
      };

      const onPointerMove = (e: React.PointerEvent) => {
        if (!dragStartRef.current || didDragRef.current) return;
        const dx = e.clientX - dragStartRef.current.x;
        const dy = e.clientY - dragStartRef.current.y;
        if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) {
          didDragRef.current = true;
          dragStartRef.current = null;
          getCurrentWindow().startDragging().catch(() => {});
        }
      };

      const onPointerUp = () => {
        if (dragStartRef.current && !didDragRef.current) {
          // Mouse didn't move enough — this was a click
          onClick();
        }
        dragStartRef.current = null;
        didDragRef.current = false;
      };

      return { onPointerDown, onPointerMove, onPointerUp };
    },
    []
  );

  return useMemo(() => ({ setModeSize, makeDragHandlers }), [setModeSize, makeDragHandlers]);
}

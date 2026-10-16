import { motion } from "framer-motion";
import type { OrbActivity } from "../types";

interface OrbProps {
  activity: OrbActivity;
  variant: "full" | "mini";
  onPointerDown: (e: React.PointerEvent) => void;
  onPointerMove: (e: React.PointerEvent) => void;
  onPointerUp: (e: React.PointerEvent) => void;
}

const orbAnimations: Record<
  OrbActivity,
  { scale: number[]; opacity: number[]; boxShadow: string[]; transition: object }
> = {
  idle: {
    scale: [0.95, 1.05, 0.95],
    opacity: [0.85, 1, 0.85],
    boxShadow: [
      "0 0 20px rgba(109,211,255,0.3), 0 0 60px rgba(155,140,255,0.15)",
      "0 0 30px rgba(109,211,255,0.5), 0 0 80px rgba(155,140,255,0.25)",
      "0 0 20px rgba(109,211,255,0.3), 0 0 60px rgba(155,140,255,0.15)",
    ],
    transition: { duration: 4, repeat: Infinity, ease: "easeInOut" },
  },
  thinking: {
    scale: [0.92, 1.08, 0.92],
    opacity: [0.9, 1, 0.9],
    boxShadow: [
      "0 0 30px rgba(109,211,255,0.6), 0 0 80px rgba(155,140,255,0.35)",
      "0 0 50px rgba(109,211,255,0.8), 0 0 120px rgba(155,140,255,0.5)",
      "0 0 30px rgba(109,211,255,0.6), 0 0 80px rgba(155,140,255,0.35)",
    ],
    transition: { duration: 1.5, repeat: Infinity, ease: "easeInOut" },
  },
  tool: {
    scale: [1.0, 1.12, 1.0],
    opacity: [1, 1, 1],
    boxShadow: [
      "0 0 40px rgba(38,208,124,0.7), 0 0 80px rgba(38,208,124,0.3)",
      "0 0 60px rgba(38,208,124,0.9), 0 0 120px rgba(38,208,124,0.5)",
      "0 0 40px rgba(38,208,124,0.7), 0 0 80px rgba(38,208,124,0.3)",
    ],
    transition: { duration: 0.8, repeat: Infinity, ease: "easeInOut" },
  },
  streaming: {
    scale: [0.97, 1.03, 0.97],
    opacity: [0.9, 1, 0.9],
    boxShadow: [
      "0 0 25px rgba(109,211,255,0.5), 0 0 70px rgba(155,140,255,0.3)",
      "0 0 40px rgba(109,211,255,0.7), 0 0 100px rgba(155,140,255,0.4)",
      "0 0 25px rgba(109,211,255,0.5), 0 0 70px rgba(155,140,255,0.3)",
    ],
    transition: { duration: 2, repeat: Infinity, ease: "easeInOut" },
  },
  error: {
    scale: [0.98, 1.02, 0.98],
    opacity: [0.3, 0.5, 0.3],
    boxShadow: [
      "0 0 15px rgba(239,68,68,0.3), 0 0 40px rgba(239,68,68,0.1)",
      "0 0 20px rgba(239,68,68,0.5), 0 0 60px rgba(239,68,68,0.2)",
      "0 0 15px rgba(239,68,68,0.3), 0 0 40px rgba(239,68,68,0.1)",
    ],
    transition: { duration: 3, repeat: Infinity, ease: "easeInOut" },
  },
  disconnected: {
    scale: [0.97, 1.0, 0.97],
    opacity: [0.25, 0.4, 0.25],
    boxShadow: [
      "0 0 10px rgba(109,211,255,0.1), 0 0 30px rgba(155,140,255,0.05)",
      "0 0 15px rgba(109,211,255,0.2), 0 0 40px rgba(155,140,255,0.1)",
      "0 0 10px rgba(109,211,255,0.1), 0 0 30px rgba(155,140,255,0.05)",
    ],
    transition: { duration: 5, repeat: Infinity, ease: "easeInOut" },
  },
};

export function Orb({
  activity,
  variant,
  onPointerDown,
  onPointerMove,
  onPointerUp,
}: OrbProps) {
  const anim = orbAnimations[activity];

  return (
    <motion.div
      className={`orb ${variant}`}
      animate={{
        scale: anim.scale,
        opacity: anim.opacity,
        boxShadow: anim.boxShadow,
      }}
      transition={anim.transition}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      whileHover={{ scale: variant === "full" ? 1.1 : 1.05 }}
    />
  );
}

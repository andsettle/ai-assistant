import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import type { ResponseBlock } from "../types";
import { ScreenshotInline } from "./ScreenshotInline";

interface ResponseAreaProps {
  responses: ResponseBlock[];
  currentResponse: string;
  isStreaming: boolean;
}

const childVariants = {
  collapsed: { opacity: 0, y: 12 },
  expanded: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: "easeOut" as const },
  },
};

export function ResponseArea({
  responses,
  currentResponse,
  isStreaming,
}: ResponseAreaProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentResponse, responses]);

  const hasContent = responses.length > 0 || currentResponse;

  return (
    <motion.div
      className="response-area"
      ref={scrollRef}
      variants={childVariants}
    >
      {!hasContent && (
        <div className="response-empty">
          <span className="response-empty-text">Ask me anything</span>
        </div>
      )}

      {responses.map((block) => (
        <motion.div
          key={block.id}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="response-block"
        >
          {block.type === "text" ? (
            <p className="response-text">{block.content}</p>
          ) : (
            <ScreenshotInline base64={block.content} />
          )}
        </motion.div>
      ))}

      {currentResponse && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="response-block current"
        >
          <p className="response-text">
            {currentResponse}
            {isStreaming && <span className="cursor-blink">|</span>}
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}

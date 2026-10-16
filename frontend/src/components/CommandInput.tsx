import { useRef, useEffect } from "react";
import { motion } from "framer-motion";

interface CommandInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  placeholder: string;
}

const childVariants = {
  collapsed: { opacity: 0, y: 12 },
  expanded: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: "easeOut" as const },
  },
};

export function CommandInput({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder,
}: CommandInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Auto-focus when mounted (panel just expanded)
    const timer = setTimeout(() => inputRef.current?.focus(), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <motion.div className="command-input-wrapper" variants={childVariants}>
      <input
        ref={inputRef}
        type="text"
        className="command-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
      />
    </motion.div>
  );
}

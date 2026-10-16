interface ScreenshotInlineProps {
  base64: string;
}

export function ScreenshotInline({ base64 }: ScreenshotInlineProps) {
  return (
    <div className="screenshot-inline">
      <img
        src={`data:image/jpeg;base64,${base64}`}
        alt="Screenshot"
        className="screenshot-img"
      />
    </div>
  );
}

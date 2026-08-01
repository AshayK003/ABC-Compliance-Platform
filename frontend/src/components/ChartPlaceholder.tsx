interface ChartPlaceholderProps {
  readonly className?: string;
  readonly height?: string;
  readonly children?: React.ReactNode;
}

export function ChartPlaceholder({ className = '', height = '300px', children }: ChartPlaceholderProps) {
  return (
    <div className={`bg-surface-container-lowest border border-outline-variant/50 rounded flex items-end p-4 gap-2 min-h-[${height}] ${className}`}>
      {children}
    </div>
  );
}
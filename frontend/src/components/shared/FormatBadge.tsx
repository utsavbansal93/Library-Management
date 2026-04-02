interface FormatBadgeProps {
  format: string;
}

export default function FormatBadge({ format }: FormatBadgeProps) {
  return (
    <span className="inline-block bg-secondary-container text-on-secondary-container font-label text-[10px] uppercase tracking-widest font-bold rounded-full px-3 py-1">
      {format}
    </span>
  );
}

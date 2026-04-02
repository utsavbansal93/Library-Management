interface ReadingStatusBadgeProps {
  status: string;
}

const STATUS_STYLES: Record<string, string> = {
  reading: 'bg-tertiary-fixed text-on-tertiary-fixed',
  finished: 'bg-primary text-on-primary',
  unread: 'bg-surface-container-highest text-on-surface-variant',
  dnf: 'bg-error text-on-error',
};

export default function ReadingStatusBadge({ status }: ReadingStatusBadgeProps) {
  const key = status.toLowerCase();
  const style = STATUS_STYLES[key] ?? STATUS_STYLES.unread;

  return (
    <span
      className={`inline-block font-label text-[10px] uppercase tracking-widest font-bold rounded-full px-3 py-1 ${style}`}
    >
      {status}
    </span>
  );
}

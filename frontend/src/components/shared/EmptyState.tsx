interface EmptyStateProps {
  icon: string;
  title: string;
  description?: string;
}

export default function EmptyState({ icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <span className="material-symbols-outlined text-5xl text-outline-variant mb-4">
        {icon}
      </span>
      <h3 className="font-headline text-xl text-on-surface mb-2">{title}</h3>
      {description && (
        <p className="font-body text-sm text-on-surface-variant max-w-sm leading-relaxed">
          {description}
        </p>
      )}
    </div>
  );
}

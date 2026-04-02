import { useState } from 'react';

interface CoverImageProps {
  artifactId: string;
  title: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const SIZE_CLASSES: Record<string, string> = {
  sm: 'w-12 h-18',
  md: 'w-32 h-48',
  lg: 'w-48 h-72',
};

function formatIcon(title: string): string {
  const lower = title.toLowerCase();
  if (lower.includes('comic') || lower.includes('graphic')) return 'menu_book';
  if (lower.includes('magazine')) return 'newspaper';
  if (lower.includes('kindle') || lower.includes('digital')) return 'tablet';
  return 'auto_stories';
}

export default function CoverImage({
  artifactId,
  title,
  className = '',
  size = 'md',
}: CoverImageProps) {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return (
      <div
        className={`aspect-[2/3] bg-surface-container-high flex items-center justify-center ${SIZE_CLASSES[size]} ${className}`}
      >
        <span className="material-symbols-outlined text-on-surface-variant text-3xl">
          {formatIcon(title)}
        </span>
      </div>
    );
  }

  return (
    <img
      src={`/api/artifacts/${artifactId}/cover`}
      alt={title}
      loading="lazy"
      onError={() => setHasError(true)}
      className={`aspect-[2/3] object-cover ${SIZE_CLASSES[size]} ${className}`}
    />
  );
}

import { useState, useEffect } from 'react';

interface CoverImageProps {
  artifactId?: string;
  workId?: string;
  title: string;
  className?: string;
  /** Cache-bust key — change to force reload (e.g. updated_at timestamp) */
  version?: string | number | null;
}

function formatIcon(title: string): { icon: string; bg: string; fg: string } {
  const lower = title.toLowerCase();
  if (lower.includes('comic') || lower.includes('graphic'))
    return { icon: 'menu_book', bg: 'bg-[#1b3a5c]', fg: 'text-[#8bb8e8]' };
  if (lower.includes('magazine'))
    return { icon: 'newspaper', bg: 'bg-[#5c1a1a]', fg: 'text-[#e88b8b]' };
  if (lower.includes('kindle') || lower.includes('digital'))
    return { icon: 'tablet', bg: 'bg-[#1a3c1a]', fg: 'text-[#8bc88b]' };
  return { icon: 'auto_stories', bg: 'bg-surface-container-high', fg: 'text-on-surface-variant' };
}

export default function CoverImage({
  artifactId,
  workId,
  title,
  className = 'w-full',
  version,
}: CoverImageProps) {
  const [hasError, setHasError] = useState(false);

  // Reset error state when the artifact/work changes or version changes
  useEffect(() => {
    setHasError(false);
  }, [artifactId, workId, version]);

  const base = artifactId
    ? `/api/artifacts/${artifactId}/cover`
    : workId
      ? `/api/works/${workId}/cover`
      : null;
  const src = base && version ? `${base}?v=${version}` : base;

  if (hasError || !src) {
    const { icon, bg, fg } = formatIcon(title);
    return (
      <div
        className={`${bg} flex flex-col items-center justify-center aspect-[2/3] overflow-hidden ${className}`}
      >
        <span className={`material-symbols-outlined ${fg} text-3xl`}>
          {icon}
        </span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={title}
      loading="lazy"
      onError={() => setHasError(true)}
      className={`object-cover aspect-[2/3] ${className}`}
    />
  );
}

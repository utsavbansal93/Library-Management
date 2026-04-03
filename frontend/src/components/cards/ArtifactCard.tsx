import { Link } from 'react-router-dom';
import type { ArtifactSummary } from '../../types';
import CoverImage from '../shared/CoverImage';
import FormatBadge from '../shared/FormatBadge';

interface ArtifactCardProps {
  artifact: ArtifactSummary;
  readingStatus?: string;
}

export default function ArtifactCard({ artifact, readingStatus }: ArtifactCardProps) {
  // Derive a display creator from volume_run or publisher
  const creatorText = artifact.volume_run?.publisher ?? artifact.publisher ?? '';

  return (
    <Link
      to={`/artifacts/${artifact.artifact_id}`}
      className="group block bg-surface-container-lowest rounded-sm shadow-[0_10px_30px_rgba(27,28,25,0.06)] overflow-hidden transition-all duration-200 hover:scale-[1.02] hover:shadow-[0_14px_40px_rgba(27,28,25,0.12)]"
    >
      {/* Cover */}
      <CoverImage
        artifactId={artifact.artifact_id}
        title={artifact.title}

        className="w-full"
      />

      {/* Info */}
      <div className="p-3 space-y-2">
        <h3 className="font-headline text-sm text-on-surface font-semibold leading-snug line-clamp-2" title={artifact.title}>
          {artifact.title}
        </h3>

        {creatorText && (
          <p className="font-body text-xs text-on-surface-variant truncate">
            {creatorText}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-1.5">
          <FormatBadge format={artifact.format} />
          {artifact.is_reprint && (
            <span className="inline-block font-label text-[10px] uppercase tracking-widest font-bold rounded-full px-3 py-1 bg-secondary text-on-secondary">
              {artifact.original_publisher ? `Reprint: ${artifact.original_publisher}` : 'Reprint'}
            </span>
          )}
          {artifact.is_lent && (
            <span className="inline-block font-label text-[10px] uppercase tracking-widest font-bold rounded-full px-3 py-1 bg-tertiary-fixed text-on-tertiary-fixed">
              Lent
            </span>
          )}
          {readingStatus && (
            <span
              className={`inline-block font-label text-[10px] uppercase tracking-widest font-bold rounded-full px-3 py-1 ${statusStyle(readingStatus)}`}
            >
              {readingStatus}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

function statusStyle(status: string): string {
  switch (status.toLowerCase()) {
    case 'reading':
      return 'bg-tertiary-fixed text-on-tertiary-fixed';
    case 'finished':
      return 'bg-primary text-on-primary';
    case 'dnf':
      return 'bg-error text-on-error';
    default:
      return 'bg-surface-container-highest text-on-surface-variant';
  }
}

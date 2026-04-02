import { Link } from 'react-router-dom';
import type { ArtifactSummary } from '../../types';
import CoverImage from '../shared/CoverImage';
import FormatBadge from '../shared/FormatBadge';

interface ArtifactListRowProps {
  artifact: ArtifactSummary;
}

export default function ArtifactListRow({ artifact }: ArtifactListRowProps) {
  return (
    <Link
      to={`/artifacts/${artifact.artifact_id}`}
      className="group flex items-center gap-4 px-4 py-3 transition-colors even:bg-surface-container-low hover:bg-surface-container-high"
    >
      {/* Small cover thumbnail */}
      <CoverImage
        artifactId={artifact.artifact_id}
        title={artifact.title}
        size="sm"
        className="rounded-sm shrink-0"
      />

      {/* Title & publisher */}
      <div className="flex-1 min-w-0">
        <h4 className="font-headline text-sm text-on-surface font-semibold truncate">
          {artifact.title}
        </h4>
        {artifact.publisher && (
          <p className="font-body text-xs text-on-surface-variant truncate mt-0.5">
            {artifact.publisher}
          </p>
        )}
      </div>

      {/* Format badge */}
      <div className="hidden sm:block shrink-0">
        <FormatBadge format={artifact.format} />
      </div>

      {/* Owner */}
      {artifact.owner && (
        <span className="hidden md:block font-body text-xs text-on-surface-variant shrink-0 w-32 truncate text-right">
          {artifact.owner}
        </span>
      )}

      {/* Arrow */}
      <span className="material-symbols-outlined text-outline-variant text-[18px] opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
        chevron_right
      </span>
    </Link>
  );
}

import { useNavigate } from 'react-router-dom';
import type { ArtifactSummary } from '../../types';
import CoverImage from '../shared/CoverImage';
import FormatBadge from '../shared/FormatBadge';

interface ArtifactListRowProps {
  artifact: ArtifactSummary;
}

export default function ArtifactListRow({ artifact }: ArtifactListRowProps) {
  const navigate = useNavigate();

  return (
    <tr
      onClick={() => navigate(`/artifacts/${artifact.artifact_id}`)}
      className="group cursor-pointer transition-colors border-b border-surface-variant/20 hover:bg-surface-container-high"
    >
      <td className="px-4 py-2">
        <div className="flex items-center gap-3">
          <div className="w-8 overflow-hidden rounded-sm shrink-0 shadow-sm">
            <CoverImage
              artifactId={artifact.artifact_id}
              title={artifact.title}
              className="w-full h-auto aspect-[2/3] object-cover"
            />
          </div>
          <h4 className="font-headline text-sm text-on-surface font-semibold line-clamp-1" title={artifact.title}>
            {artifact.title}
          </h4>
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <FormatBadge format={artifact.format} />
      </td>
      <td className="hidden px-4 py-3 md:table-cell max-w-[180px]">
        {artifact.publisher && (
          <span className="font-body text-xs text-on-surface-variant truncate block">
            {artifact.publisher}
          </span>
        )}
      </td>
      <td className="hidden px-4 py-3 lg:table-cell whitespace-nowrap">
        {artifact.owner && (
          <span className="font-body text-xs text-on-surface-variant">
            {artifact.owner}
          </span>
        )}
      </td>
      <td className="px-4 py-3 text-right">
        <span className="material-symbols-outlined text-outline-variant text-[18px] opacity-0 group-hover:opacity-100 transition-opacity">
          chevron_right
        </span>
      </td>
    </tr>
  );
}

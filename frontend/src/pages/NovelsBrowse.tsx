import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listArtifacts } from '../api/artifacts';
import CoverImage from '../components/shared/CoverImage';
import type { ArtifactSummary } from '../types';

const NOVEL_FORMATS = ['Hardcover', 'Paperback', 'Kindle', 'Audible'];

export default function NovelsBrowse() {
  // Fetch all novel-like formats in parallel
  const queries = NOVEL_FORMATS.map((fmt) =>
    useQuery({
      queryKey: ['artifacts', { format: fmt }],
      queryFn: () => listArtifacts({ format: fmt }),
    }),
  );

  const isLoading = queries.some((q) => q.isLoading);
  const isError = queries.some((q) => q.isError);
  const firstError = queries.find((q) => q.error)?.error;

  const allArtifacts: ArtifactSummary[] = queries
    .flatMap((q) => q.data ?? [])
    .sort((a, b) => a.title.localeCompare(b.title));

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Novels</h1>
        <p className="mt-2 font-body text-base text-on-surface-variant">
          {isLoading
            ? 'Loading...'
            : `${allArtifacts.length} novel${allArtifacts.length !== 1 ? 's' : ''} in your library`}
        </p>
      </header>

      {isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="aspect-[2/3] animate-pulse rounded-2xl bg-surface-container-low" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-2xl bg-error-container p-6 text-on-error-container">
          <p className="font-body text-sm">
            Failed to load novels. {firstError instanceof Error ? firstError.message : 'Unknown error.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && allArtifacts.length === 0 && (
        <div className="flex flex-col items-center gap-4 py-20">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant">
            auto_stories
          </span>
          <p className="font-body text-sm text-on-surface-variant">
            No novels in your library yet.
          </p>
        </div>
      )}

      {!isLoading && !isError && allArtifacts.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {allArtifacts.map((artifact) => (
            <Link
              key={artifact.artifact_id}
              to={`/artifacts/${artifact.artifact_id}`}
              className="group overflow-hidden rounded-2xl bg-surface-container-lowest transition-shadow hover:shadow-md"
            >
              <CoverImage
                artifactId={artifact.artifact_id}
                title={artifact.title}
                size="md"
                className="w-full"
              />
              <div className="p-3">
                <p className="font-body text-sm font-medium text-on-surface line-clamp-2 group-hover:underline">
                  {artifact.title}
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <span className="rounded-full bg-surface-container-highest px-2 py-0.5 font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                    {artifact.format}
                  </span>
                  {artifact.publisher && (
                    <span className="font-label text-[10px] text-secondary">{artifact.publisher}</span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

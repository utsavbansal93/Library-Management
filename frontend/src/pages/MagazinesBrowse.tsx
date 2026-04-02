import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listArtifacts } from '../api/artifacts';
import CoverImage from '../components/shared/CoverImage';

export default function MagazinesBrowse() {
  const {
    data: magazines,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['artifacts', { format: 'Magazine' }],
    queryFn: () => listArtifacts({ format: 'Magazine' }),
  });

  const items = magazines ?? [];

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">Magazines</h1>
        <p className="mt-2 font-body text-base text-on-surface-variant">
          {isLoading
            ? 'Loading...'
            : `${items.length} magazine${items.length !== 1 ? 's' : ''} in your library`}
        </p>
      </header>

      {isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="aspect-[2/3] animate-pulse rounded-2xl bg-surface-container-low" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-2xl bg-error-container p-6 text-on-error-container">
          <p className="font-body text-sm">
            Failed to load magazines. {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <div className="flex flex-col items-center gap-4 py-20">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant">
            newspaper
          </span>
          <p className="font-body text-sm text-on-surface-variant">
            No magazines in your library yet.
          </p>
        </div>
      )}

      {!isLoading && !isError && items.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {items.map((artifact) => (
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
                {artifact.publisher && (
                  <p className="mt-1 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
                    {artifact.publisher}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

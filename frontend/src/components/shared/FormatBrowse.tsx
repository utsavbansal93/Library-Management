import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listArtifacts } from '../../api/artifacts';
import CoverImage from './CoverImage';
import Pagination from './Pagination';

const PAGE_SIZE = 40;

interface FormatBrowseProps {
  title: string;
  category: string;
  emptyIcon?: string;
  emptyLabel?: string;
}

export default function FormatBrowse({
  title,
  category,
  emptyIcon = 'auto_stories',
  emptyLabel,
}: FormatBrowseProps) {
  const [page, setPage] = useState(1);
  const offset = (page - 1) * PAGE_SIZE;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['artifacts', { category, offset, limit: PAGE_SIZE }],
    queryFn: () => listArtifacts({ category, offset, limit: PAGE_SIZE }),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="min-h-screen bg-surface px-6 py-10 lg:px-12">
      <header className="mb-10">
        <h1 className="font-headline text-5xl text-primary">{title}</h1>
        <p className="mt-2 font-body text-base text-on-surface-variant">
          {isLoading
            ? 'Loading...'
            : `${total} item${total !== 1 ? 's' : ''} in your library`}
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
            Failed to load {title.toLowerCase()}.{' '}
            {error instanceof Error ? error.message : 'Unknown error.'}
          </p>
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <div className="flex flex-col items-center gap-4 py-20">
          <span className="material-symbols-outlined text-5xl text-on-surface-variant">
            {emptyIcon}
          </span>
          <p className="font-body text-sm text-on-surface-variant">
            No {emptyLabel ?? title.toLowerCase()} in your library yet.
          </p>
        </div>
      )}

      {!isLoading && !isError && items.length > 0 && (
        <>
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
                      <span className="font-label text-[10px] text-secondary">
                        {artifact.publisher}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="mt-8">
              <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
